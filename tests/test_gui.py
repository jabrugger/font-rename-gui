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
from font_rename_gui.app import MainWindow
from font_rename_gui.model import Options, build_arguments, unique_folders


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
        self.folder = Path(self.temp.name)
        self.window = MainWindow(persist=False)

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
        with self.assertRaises(ValueError):
            build_arguments([self.folder], Options(log_path=str(self.folder/'font.ttf')), True)

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


if __name__ == '__main__':
    unittest.main()
