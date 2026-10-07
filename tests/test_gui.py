import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from font_rename_neo_gui.app import MainWindow
from font_rename_neo_gui.model import Options, build_arguments, unique_folders, default_log_directory


def make_font(path):
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(['.notdef'])
    fb.setupCharacterMap({})
    fb.setupGlyf({'.notdef': TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({'.notdef': (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName':'Test', 'styleName':'Regular', 'fullName':'Test Regular', 'psName':'Test-Regular'})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    fb.save(path)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name).resolve()
        self.window = MainWindow(persist=False)
        self.window.log_path.setText(str(self.folder/'logs'))

    def tearDown(self):
        self.assertFalse(self.window._busy(), 'Worker must finish before teardown')
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def run_window(self, apply=False):
        self.window.start_run(apply)
        self.assertIsNotNone(self.window.runner)
        loop = QEventLoop()
        self.window.runner.finished.connect(loop.quit)
        QTimer.singleShot(20000, loop.quit)
        loop.exec()
        self.app.processEvents()
        self.assertFalse(self.window._busy(), 'Engine did not finish in time')

    def test_overlap_selection_scans_each_tree_once(self):
        child = self.folder/'child'
        child.mkdir()
        self.assertEqual(unique_folders([child, self.folder, self.folder]), [self.folder])

    def test_options_map_to_cli_without_shell_quoting(self):
        folder = self.folder/'Fonts with spaces'
        folder.mkdir()
        args, log = build_arguments([folder], Options(False, False, False, False), True)
        self.assertEqual(args[0], str(folder))
        self.assertIn('--apply', args)
        self.assertIn('--keep-duplicates', args)
        self.assertIn('--no-transliterate', args)
        self.assertNotIn('--normalize-internal', args)
        self.assertIsNone(log)

    def test_bad_log_path_rejected_before_processing(self):
        destination=self.folder/'font.ttf'
        destination.write_bytes(b'keep')
        with self.assertRaises(ValueError):
            build_arguments([self.folder], Options(log_directory=str(destination)), True)
        self.assertEqual(destination.read_bytes(),b'keep')

    def test_apply_requires_preview_and_options_change_invalidates_it(self):
        self.window.add_folder_path(str(self.folder))
        self.assertFalse(self.window.apply_button.isEnabled())
        self.window.start_run(True)
        self.assertFalse(self.window._busy())
        self.run_window()
        self.assertTrue(self.window.apply_button.isEnabled())
        self.window.checkboxes['normalize'].setChecked(False)
        self.assertFalse(self.window.apply_button.isEnabled())

    def test_preview_then_apply_uses_real_engine_and_utf8_log(self):
        original_path = self.folder/'source.ttf'
        make_font(original_path)
        original = original_path.read_bytes()
        shutil.copyfile(original_path, self.folder/'copy.ttf')
        self.window.add_folder_path(str(self.folder))
        self.run_window()
        self.assertEqual(original_path.read_bytes(), original)
        self.assertEqual(len(list(self.folder.glob('*.ttf'))), 2)
        self.assertIn('RENAME:', self.window.output.toPlainText())
        self.assertTrue(self.window.last_log.exists())
        self.run_window(True)
        self.assertEqual(self.window.result, 0)
        self.assertEqual(len(list(self.folder.glob('*.ttf'))), 1)
        self.assertTrue((self.folder/'Test Regular.ttf').exists())
        self.assertIn('=== END ', self.window.last_log.read_text(encoding='utf-8'))
        self.assertFalse(self.window.apply_button.isEnabled())

    def test_log_view_is_bounded(self):
        self.window._append_output('\n'.join(str(i) for i in range(10000)))
        self.assertLessEqual(self.window.output.document().blockCount(), 3000)
        self.assertIn('9999', self.window.output.toPlainText())
        self.assertNotIn('\n0\n', self.window.output.toPlainText())

    def test_cancellation_requests_file_without_killing_worker(self):
        self.window.add_folder_path(str(self.folder))
        self.window.cancel_file = self.folder/'cancel.flag'
        self.window.runner = object()
        self.window._cancel()
        self.assertTrue(self.window.cancel_file.is_file())
        self.assertFalse(self.window.cancel_button.isEnabled())
        self.window.runner = None
        self.window.cancel_file = None

    def test_language_change_updates_controls(self):
        self.window.language_picker.setCurrentIndex(1)
        self.assertEqual(self.window.preview_button.text(), 'Preview')
        self.window.language_picker.setCurrentIndex(0)
        self.assertEqual(self.window.preview_button.text(), 'Vista previa')

    def test_clear_screen_removes_placeholder_and_preserves_log(self):
        log = self.folder/'test.log'
        log.write_text('keep this log',encoding='utf-8')
        self.window.last_log = log
        self.window._append_output('visible activity')
        self.window.clear_button.click()
        self.assertEqual(self.window.output.toPlainText(), '')
        self.assertEqual(self.window.output.placeholderText(), '')
        self.assertEqual(log.read_text(encoding='utf-8'), 'keep this log')
        self.window.runner=object()
        self.window._refresh_controls()
        self.assertTrue(self.window.clear_button.isEnabled())
        self.window.runner=None

    def test_one_folder_replaces_previous_selection(self):
        child = self.folder/'child'
        child.mkdir()
        self.window.add_folder_path(str(self.folder))
        self.window.add_folder_path(str(child))
        self.assertEqual(self.window.folder_paths(), [str(child)])
        self.assertTrue(self.window.recursive.isChecked())

    def test_central_log_and_recursion_keep_global_deduplication(self):
        child=self.folder/'child'
        child.mkdir()
        make_font(self.folder/'root.ttf')
        shutil.copy2(self.folder/'root.ttf',child/'child.ttf')
        self.window.add_folder_path(str(self.folder))
        self.window.recursive.setChecked(False)
        self.run_window()
        log=self.window.last_log
        self.assertEqual(log.parent,self.folder/'logs')
        self.assertNotIn('child.ttf',log.read_text(encoding='utf-8'))
        self.window.recursive.setChecked(True)
        self.run_window()
        self.assertEqual(self.window.last_log,log)
        text=log.read_text(encoding='utf-8')
        self.assertIn('root.ttf',text)
        self.assertIn('child.ttf',text)
        self.assertEqual(len(list(self.folder.rglob('*.ttf'))),2)
        self.assertFalse((self.folder/'BAK').exists())
        self.assertFalse((child/'BAK').exists())
        self.run_window(True)
        self.assertEqual(self.window.result,0)
        self.assertEqual(len(list(self.folder.rglob('*.ttf'))),1)

    def test_default_log_directory_uses_frozen_executable_not_working_folder(self):
        import sys
        exe=self.folder/'portable'/'FontRenameNeo.exe'
        with patch.object(sys,'frozen',True,create=True), patch.object(sys,'executable',str(exe)):
            self.assertEqual(default_log_directory(),exe.parent/'logs')
            args,log=build_arguments([self.folder],Options())
            self.assertEqual(log.parent,exe.parent/'logs')
            self.assertIn('--log',args)
            self.assertNotIn('--log-per-folder',args)

    def test_disabled_logging_does_not_create_directory(self):
        destination=self.folder/'disabled-logs'
        args,log=build_arguments([self.folder],Options(save_log=False,log_directory=str(destination)))
        self.assertIsNone(log)
        self.assertFalse(destination.exists())

    def test_folder_chooser_configures_log_directory(self):
        from PySide6.QtWidgets import QFileDialog
        with patch.object(QFileDialog,'getExistingDirectory',return_value=str(self.folder/'chosen')):
            self.window._browse_log()
        self.assertEqual(self.window.options().log_directory,str(self.folder/'chosen'))

    def test_qt_dialog_buttons_follow_selected_language(self):
        from PySide6.QtWidgets import QMessageBox
        dialog=QMessageBox(self.window)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.assertEqual(dialog.button(QMessageBox.StandardButton.Yes).text().replace('&',''),'S\u00ed')
        self.window.language_picker.setCurrentIndex(1)
        dialog=QMessageBox(self.window)
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.assertEqual(dialog.button(QMessageBox.StandardButton.Yes).text().replace('&',''),'Yes')
        self.assertIn('other writing systems',self.window.checkboxes['transliterate'].toolTip())
        self.window.language_picker.setCurrentIndex(0)
        self.assertEqual(self.window.language_picker.itemText(1),'Ingl\u00e9s')

    def test_table_preview_combines_rename_and_internal_edits(self):
        view=self.window.preview_view
        view.consume("RENAME:\n  CURRENT: 'old.ttf'\n  NEW: 'New.ttf'\n  FOLDER: C:\\Fonts\nINTERNAL:\n  FILE: New.ttf\n  FOLDER: C:\\Fonts\n  NAME ID 1:\n    CURRENT: ' New '\n    NEW: 'New'\n")
        view.finish()
        self.assertEqual(len(view.rows),1)
        self.assertEqual(view.rows[0]['actions'],['rename','internal'])
        self.assertEqual(view.rows[0]['current'],'old.ttf')
        self.assertEqual(view.rows[0]['new'],'New.ttf')
        view.table.selectRow(0)
        self.assertIn('ACTUAL:',view.details.toPlainText())
        view.search.setText('missing')
        self.assertEqual(view.proxy.rowCount(),0)
        view.search.clear()
        view.action.setCurrentIndex(view.action.findData('error'))
        self.assertEqual(view.proxy.rowCount(),0)
        view.action.setCurrentIndex(view.action.findData('internal'))
        self.assertEqual(view.proxy.rowCount(),1)
        self.assertIsNone(self.window.preview_signature)

    def test_table_preview_handles_duplicates_errors_and_batch_boundaries(self):
        view=self.window.preview_view
        view.consume('DUPLICATE:\n  CURRENT: copy.ttf')
        view.consume('  FOLDER: C:\\Fonts\n  KEEP: C:\\Fonts\\original.ttf\nERROR (kept): C:\\Fonts\\broken.ttf: bad font\n')
        view.finish()
        self.assertEqual(len(view.rows),2)
        self.assertEqual(view.rows[0]['actions'],['duplicate'])
        self.assertEqual(view.rows[1]['current'],'broken.ttf')
        view.set_language('en')
        self.assertIn('errors',view.summary.text())

    def test_completed_preview_rows_are_confirmed_by_worker(self):
        from fontTools.ttLib import TTFont
        source=self.folder/'source.ttf'
        make_font(source)
        with TTFont(source,recalcTimestamp=False) as font:
            for record in font['name'].names:
                if record.nameID==1:
                    record.string=(' '+record.toUnicode()+' ').encode(record.getEncoding())
            font.save(source)
        self.window.add_folder_path(str(self.folder))
        self.window.start_run(False)
        self.assertEqual(self.window.view_stack.currentIndex(),0)
        loop=QEventLoop()
        self.window.runner.finished.connect(loop.quit)
        QTimer.singleShot(20000,loop.quit)
        loop.exec()
        self.app.processEvents()
        self.assertEqual(self.window.view_stack.currentIndex(),1)
        self.assertIn('internal',self.window.preview_view.rows[0]['actions'])
        self.run_window(True)
        self.assertEqual(self.window.preview_view.rows[0]['status'],'done')
        self.assertEqual(self.window.preview_view.rows[0]['results'],{'file':'done','internal':'done'})
        self.assertEqual(self.window.view_stack.currentIndex(),1)
        self.assertNotIn('GUI_EVENT:',self.window.output.toPlainText())

    def test_failure_never_gets_a_green_completion_mark(self):
        from fontTools.ttLib import TTFont
        source=self.folder/'source.ttf'
        make_font(source)
        with TTFont(source,recalcTimestamp=False) as font:
            for record in font['name'].names:
                if record.nameID==1:
                    record.string=(' '+record.toUnicode()+' ').encode(record.getEncoding())
            font.save(source)
        self.window.add_folder_path(str(self.folder))
        self.run_window()
        backup=self.folder/'BAK'/'Test Regular.ttf.original.bak'
        backup.parent.mkdir()
        backup.write_bytes(b'Existing backup must survive')
        self.run_window(True)
        row=self.window.preview_view.rows[0]
        self.assertEqual(row['status'],'error')
        self.assertEqual(row['results']['file'],'done')
        self.assertEqual(row['results']['internal'],'error')
        self.assertEqual(backup.read_bytes(),b'Existing backup must survive')

    def test_unfinished_operations_remain_not_processed(self):
        view=self.window.preview_view
        view.consume("RENAME:\n  CURRENT: 'old.ttf'\n  NEW: 'New.ttf'\n  FOLDER: C:\\Fonts\n")
        view.finish()
        view.begin_apply()
        self.assertEqual(view.rows[0]['status'],'pending')
        view.finish_apply()
        self.assertEqual(view.rows[0]['status'],'not_processed')
        self.assertEqual(self.window.cancel_button.text(),'Detener proceso')
        self.assertIn('no deshace',self.window.cancel_button.toolTip())

    def test_active_action_button_becomes_stop(self):
        self.window.add_folder_path(str(self.folder))
        self.window.runner=object()
        self.window.cancel_file=self.folder/'stop.flag'
        self.window.running_apply=False
        self.window._refresh_controls()
        self.assertEqual(self.window.preview_button.text(),'Detener')
        self.assertTrue(self.window.preview_button.isEnabled())
        self.assertFalse(self.window.apply_button.isEnabled())
        self.window.preview_button.click()
        self.assertTrue(self.window.cancel_file.exists())
        self.assertFalse(self.window.preview_button.isEnabled())
        self.window.cancel_file.unlink()
        self.window.running_apply=True
        self.window._refresh_controls()
        self.assertEqual(self.window.apply_button.text(),'Detener')
        self.assertTrue(self.window.apply_button.isEnabled())
        self.assertFalse(self.window.preview_button.isEnabled())
        self.window.apply_button.click()
        self.assertTrue(self.window.cancel_file.exists())
        self.window.runner=None
        self.window.cancel_file=None
        self.window._refresh_controls()
        self.assertEqual(self.window.preview_button.text(),'Vista previa')
        self.assertFalse(self.window.preview_button.icon().isNull())
        self.assertTrue(self.window.cancel_button.isHidden())

    def test_collection_member_statuses_are_independent(self):
        view=self.window.preview_view
        view.consume('EXTRACT:\n  COLLECTION: family.ttc\n  NEW: one.ttf\n  FOLDER: C:\\Fonts\nEXTRACT:\n  COLLECTION: family.ttc\n  NEW: two.ttf\n  FOLDER: C:\\Fonts\nINTERNAL:\n  FILE: one.ttf\n  FOLDER: C:\\Fonts\nINTERNAL:\n  FILE: two.ttf\n  FOLDER: C:\\Fonts\n')
        view.finish()
        self.assertEqual(len(view.rows),3)
        self.assertIn('two.ttf',view.rows[0]['new'])
        view.begin_apply()
        view.apply_event({'path':r'C:\Fonts\one.ttf','phase':'internal','status':'error'})
        view.apply_event({'path':r'C:\Fonts\two.ttf','phase':'internal','status':'done'})
        self.assertEqual(view.rows[1]['status'],'error')
        self.assertEqual(view.rows[2]['status'],'done')

    def test_filter_selection_and_details_stay_connected(self):
        view=self.window.preview_view
        view.consume("RENAME:\n  CURRENT: 'good.ttf'\n  NEW: 'Good.ttf'\n  FOLDER: C:\\Fonts\nERROR (kept): C:\\Fonts\\broken.ttf: bad header\n")
        view.finish()
        view.action.setCurrentIndex(view.action.findData('error'))
        self.assertEqual(view.proxy.rowCount(),1)
        self.assertIn('broken.ttf',view.detail_caption.text())
        self.assertIn('bad header',view.details.toPlainText())
        self.assertNotIn('Good.ttf',view.details.toPlainText())
        view.search.setText('not-present')
        self.assertEqual(view.details.toPlainText(),'')
        self.assertNotIn('broken.ttf',view.detail_caption.text())
        view.search.clear()
        view.refresh()
        self.assertIn('broken.ttf',view.detail_caption.text())
        self.assertGreaterEqual(view.details.minimumHeight(),200)

    def test_footer_links_to_both_repositories(self):
        self.assertTrue(self.window.footer.openExternalLinks())
        self.assertIn('href="https://github.com/jabrugger/font-rename-neo-gui"',self.window.footer.text())
        self.assertIn('href="https://github.com/jabrugger/font-rename-neo"',self.window.footer.text())

    def test_help_and_window_icon(self):
        self.assertEqual(self.window.language_picker.itemText(0),'Español')
        self.assertFalse(hasattr(self.window,'badge'))
        self.assertIn('colección', self.window.t('subtitle'))
        self.assertIn('chino',self.window.checkboxes['transliterate'].toolTip())
        self.assertFalse(self.window.windowIcon().isNull())

    def test_apply_without_preview_is_opt_in_and_confirms(self):
        make_font(self.folder/'source.ttf')
        self.window.add_folder_path(str(self.folder))
        self.assertFalse(self.window.skip_preview.isChecked())
        self.assertFalse(self.window.apply_button.isEnabled())
        self.window.skip_preview.setChecked(True)
        self.assertTrue(self.window.apply_button.isEnabled())
        from PySide6.QtWidgets import QMessageBox
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No) as confirm:
            self.window.apply_button.click()
            confirm.assert_called_once()
            self.assertEqual(confirm.call_args.args[-1], QMessageBox.StandardButton.No)
            self.assertIn('puede renombrar',confirm.call_args.args[2])
        self.assertTrue((self.folder/'source.ttf').exists())
        self.run_window(True)
        self.assertEqual(self.window.result,0)
        self.assertTrue((self.folder/'Test Regular.ttf').exists())

    def test_neo_identity_is_separate_from_legacy(self):
        from font_rename_neo_gui.model import worker_command
        from font_rename_neo_gui import worker
        self.assertEqual(self.window.windowTitle(), 'Font Rename Neo')
        self.assertEqual(self.window.settings.applicationName(), 'FontRenameNeoGUI')
        self.assertTrue(worker.engine.__name__.startswith('font_rename_neo.'))
        self.assertIn('font_rename_neo_gui.worker', worker_command())
        self.assertIn('font-rename-neo 0.4.0', self.window.footer.text())


if __name__ == '__main__':
    unittest.main()
