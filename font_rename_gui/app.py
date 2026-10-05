import re
import sys
import tempfile
from pathlib import Path
from importlib.metadata import version

from PySide6.QtCore import QLocale, QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QTextCursor
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSplitter, QVBoxLayout, QWidget)

from . import __version__
from .model import Options, build_arguments, unique_folders, worker_command
from .runner import EngineRunner

TEXT = {
 'es': {
  'subtitle':'Ordená tu colección de fuentes.', 'folders':'Carpetas',
  'folders_hint':'Incluye las subcarpetas. Los respaldos BAK quedan excluidos.',
  'add':'Agregar carpeta', 'remove':'Quitar', 'options':'Opciones',
  'normalize':'Limpiar nombres internos', 'normalize_tip':'Conserva el original en una subcarpeta BAK.',
  'dedup':'Eliminar duplicados idénticos', 'dedup_tip':'Solo elimina copias con exactamente los mismos bytes.',
  'transliterate':'Transliterar nombres', 'transliterate_tip':'Agrega un nombre latino y conserva el original entre corchetes.',
  'save_log':'Guardar log completo', 'log_hint':'Automático en la primera carpeta seleccionada',
  'browse_log':'Elegir archivo de log', 'output':'Actividad', 'clear':'Limpiar pantalla',
  'output_hint':'La pantalla conserva las últimas 3.000 líneas. El log guarda la salida completa.',
  'empty':'Agregá una carpeta y revisá la vista previa antes de aplicar cambios.',
  'preview':'Vista previa', 'apply':'Aplicar cambios', 'cancel':'Cancelar', 'open_log':'Abrir log',
  'ready':'Listo para revisar', 'previewing':'Generando vista previa…', 'applying':'Aplicando cambios…',
  'cancelling':'Cancelando al terminar la fuente en curso…', 'cancelled':'Cancelado. Los cambios terminados se conservan.',
  'preview_done':'Vista previa terminada. Podés aplicar los cambios.', 'preview_issues':'Vista previa terminada con errores. Revisá el log.',
  'done':'Ejecución terminada.', 'issues':'Ejecución terminada con errores. Revisá el log.', 'failed':'No se pudo ejecutar el motor.',
  'confirm_title':'Aplicar cambios',
  'confirm':'Se renombrarán archivos y se aplicarán las opciones seleccionadas.\nLos respaldos BAK cubren cambios internos; el borrado de duplicados no tiene deshacer.\n\n¿Aplicar a las carpetas de la vista previa?',
  'invalid':'Revisá la selección', 'close_title':'Ejecución en curso',
  'close':'Para cerrar, se cancelará entre fuentes. Los cambios ya terminados se conservarán. ¿Solicitar la cancelación?',
  'summary':'{changes} cambios · {duplicates} duplicados · {errors} errores',
  'select_folder':'Elegir carpeta de fuentes', 'choose_log':'Guardar log', 'idle':'PREVIEW FIRST',
 },
 'en': {
  'subtitle':'Bring order to your font collection.', 'folders':'Folders',
  'folders_hint':'Includes subfolders. BAK backups are excluded.',
  'add':'Add folder', 'remove':'Remove', 'options':'Options',
  'normalize':'Clean internal names', 'normalize_tip':'Keeps the original in a BAK subfolder.',
  'dedup':'Remove identical duplicates', 'dedup_tip':'Only removes copies with exactly the same bytes.',
  'transliterate':'Transliterate names', 'transliterate_tip':'Adds a Latin name and keeps the original in brackets.',
  'save_log':'Save complete log', 'log_hint':'Automatic in the first selected folder',
  'browse_log':'Choose log file', 'output':'Activity', 'clear':'Clear screen',
  'output_hint':'The screen keeps the latest 3,000 lines. The log keeps the complete output.',
  'empty':'Add a folder and review the preview before applying changes.',
  'preview':'Preview', 'apply':'Apply changes', 'cancel':'Cancel', 'open_log':'Open log',
  'ready':'Ready to preview', 'previewing':'Generating preview…', 'applying':'Applying changes…',
  'cancelling':'Cancelling after the current font…', 'cancelled':'Cancelled. Completed changes are retained.',
  'preview_done':'Preview finished. You can apply changes.', 'preview_issues':'Preview finished with errors. Review the log.',
  'done':'Run finished.', 'issues':'Run finished with errors. Review the log.', 'failed':'The engine could not be started.',
  'confirm_title':'Apply changes',
  'confirm':'Files will be renamed and selected options applied.\nBAK backups cover internal changes; duplicate removal has no undo.\n\nApply to the folders in this preview?',
  'invalid':'Check your selection', 'close_title':'Run in progress',
  'close':'Closing requests cancellation between fonts. Completed changes will be retained. Request cancellation?',
  'summary':'{changes} changes · {duplicates} duplicates · {errors} errors',
  'select_folder':'Choose a font folder', 'choose_log':'Save log', 'idle':'PREVIEW FIRST',
 }
}

STYLE = '''
QWidget { background:#171c23; color:#e6e9ed; font-family:"Segoe UI"; font-size:13px; }
QMainWindow { background:#171c23; }
QFrame#panel { background:#202730; border:1px solid #323b48; border-radius:10px; }
QFrame#panel QWidget { background:transparent; }
QLabel#title { font-size:30px; font-weight:650; }
QLabel#section { font-size:16px; font-weight:600; }
QLabel#muted { color:#a2acba; font-size:12px; }
QLabel#badge { background:#303742; color:#e2b97b; padding:7px 12px; border-radius:6px; font-size:11px; }
QListWidget, QPlainTextEdit, QLineEdit { background:#171c23; border:1px solid #394350; border-radius:6px; padding:9px; }
QListWidget::item { padding:10px; border-bottom:1px solid #2b333f; }
QListWidget::item:selected { background:#394758; }
QPushButton { background:#303a47; border:1px solid #465263; padding:9px 16px; border-radius:6px; }
QPushButton:hover { background:#3c4858; }
QPushButton:disabled { color:#78828f; background:#252d38; border-color:#323b48; }
QPushButton#primary { color:#181c22; background:#e2b97b; font-weight:600; border-color:#e2b97b; }
QPushButton#primary:hover { background:#f0cc94; }
QPushButton#primary:disabled { background:#574d3d; color:#a39784; border-color:#574d3d; }
QCheckBox { padding:3px 0; spacing:9px; min-height:24px; }
QCheckBox::indicator { width:16px; height:16px; }
QComboBox { background:#252e3a; padding:6px 12px; border:1px solid #465263; border-radius:5px; }
QComboBox QAbstractItemView { background:#252e3a; selection-background-color:#465263; }
QProgressBar { background:#252e3a; border:0; border-radius:3px; max-height:5px; }
QProgressBar::chunk { background:#e2b97b; }
QScrollBar:vertical { width:12px; background:#171c23; }
QScrollBar::handle:vertical { background:#465263; border-radius:5px; min-height:20px; }
QSplitter::handle { background:#171c23; }
'''


class MainWindow(QMainWindow):
    def __init__(self, persist=True):
        super().__init__()
        self.persist = persist
        self.settings = QSettings('jabrugger', 'FontRenamerGUI')
        system_language = 'es' if QLocale.system().language() == QLocale.Language.Spanish else 'en'
        self.language = self.settings.value('language', system_language) if persist else 'es'
        if self.language not in TEXT:
            self.language = system_language
        self.runner = None
        self.cancel_temp = None
        self.cancel_file = None
        self.last_log = None
        self.preview_signature = None
        self.running_apply = False
        self.close_pending = False
        self.result = None
        self.setWindowTitle('Font Renamer')
        self.resize(1120, 850)
        self.setMinimumSize(940, 700)
        self.setStyleSheet(STYLE)
        self._build()
        self._translate()
        if persist:
            for folder in self.settings.value('folders', [], type=list):
                if Path(folder).is_dir():
                    self.folders.addItem(folder)
            for key, checkbox in self.checkboxes.items():
                checkbox.setChecked(self.settings.value(key, True, type=bool))
            self.log_path.setText(self.settings.value('log_path', ''))
        self._refresh_controls()

    def t(self, key):
        return TEXT[self.language][key]

    def _panel(self, title_key):
        panel = QFrame()
        panel.setObjectName('panel')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(9)
        label = QLabel()
        label.setObjectName('section')
        self.labels.append((label, title_key))
        layout.addWidget(label)
        return panel, layout

    def _label(self, key, muted=True):
        label = QLabel()
        label.setWordWrap(True)
        if muted:
            label.setObjectName('muted')
        self.labels.append((label, key))
        return label

    def _button(self, key, callback):
        button = QPushButton()
        button.clicked.connect(callback)
        self.buttons.append((button, key))
        return button

    def _build(self):
        self.labels, self.buttons = [], []
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(26, 22, 26, 20)
        layout.setSpacing(16)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel('Font Renamer')
        title.setObjectName('title')
        heading.addWidget(title)
        heading.addWidget(self._label('subtitle'))
        header.addLayout(heading)
        header.addStretch()
        self.badge = self._label('idle', False)
        self.badge.setObjectName('badge')
        header.addWidget(self.badge)
        self.language_picker = QComboBox()
        self.language_picker.addItem('Español', 'es')
        self.language_picker.addItem('English', 'en')
        self.language_picker.setCurrentIndex(0 if self.language == 'es' else 1)
        self.language_picker.currentIndexChanged.connect(self._change_language)
        header.addWidget(self.language_picker)
        layout.addLayout(header)
        split = QSplitter(Qt.Orientation.Horizontal)
        folders_panel, fl = self._panel('folders')
        fl.addWidget(self._label('folders_hint'))
        self.folders = QListWidget()
        self.folders.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.folders.itemSelectionChanged.connect(self._refresh_controls)
        fl.addWidget(self.folders, 1)
        row = QHBoxLayout()
        self.add_button = self._button('add', self._add_folder)
        self.remove_button = self._button('remove', self._remove_folders)
        row.addWidget(self.add_button)
        row.addWidget(self.remove_button)
        row.addStretch()
        fl.addLayout(row)
        options_panel, ol = self._panel('options')
        self.checkboxes = {}
        for key, tip in [('normalize', 'normalize_tip'), ('dedup', 'dedup_tip'), ('transliterate', 'transliterate_tip'), ('save_log', None)]:
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._invalidate_preview)
            self.labels.append((checkbox, key))
            self.checkboxes[key] = checkbox
            ol.addWidget(checkbox)
            if tip:
                ol.addWidget(self._label(tip))
        log_row = QHBoxLayout()
        self.log_path = QLineEdit()
        self.log_path.setMinimumHeight(38)
        self.log_path.textChanged.connect(self._invalidate_preview)
        self.log_browse = QPushButton('…')
        self.log_browse.setMinimumHeight(38)
        self.log_browse.setMaximumWidth(40)
        self.log_browse.clicked.connect(self._browse_log)
        log_row.addWidget(self.log_path)
        log_row.addWidget(self.log_browse)
        ol.addLayout(log_row)
        ol.addStretch()
        split.addWidget(folders_panel)
        split.addWidget(options_panel)
        split.setSizes([630, 420])
        layout.addWidget(split, 3)
        activity_panel, al = self._panel('output')
        toolbar = QHBoxLayout()
        toolbar.addWidget(self._label('output_hint'))
        toolbar.addStretch()
        self.clear_button = self._button('clear', self._clear_output)
        toolbar.addWidget(self.clear_button)
        al.addLayout(toolbar)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(3000)
        self.output.setFont(QFont('Consolas', 10))
        self.output.setPlaceholderText(self.t('empty'))
        al.addWidget(self.output, 1)
        layout.addWidget(activity_panel, 4)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status_key = 'ready'
        self.status.setText(self.t(self.status_key))
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.open_log_button = self._button('open_log', self._open_log)
        actions.addWidget(self.open_log_button)
        actions.addStretch()
        self.cancel_button = self._button('cancel', self._cancel)
        self.preview_button = self._button('preview', lambda: self.start_run(False))
        self.apply_button = self._button('apply', self._confirm_apply)
        self.apply_button.setObjectName('primary')
        for button in (self.cancel_button, self.preview_button, self.apply_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        try:
            engine_version = version('font-rename-fm')
        except Exception:
            engine_version = '?'
        footer = QLabel(f'GUI {__version__}  ·  font-rename-fm {engine_version}  ·  MIT')
        footer.setObjectName('muted')
        layout.addWidget(footer)

    def _translate(self):
        for widget, key in self.labels:
            widget.setText(self.t(key))
        for button, key in self.buttons:
            button.setText(self.t(key))
        self.log_path.setPlaceholderText(self.t('log_hint'))
        self.log_browse.setToolTip(self.t('browse_log'))
        self.output.setPlaceholderText(self.t('empty'))
        self.status.setText(self.t(self.status_key))

    def _change_language(self):
        self.language = self.language_picker.currentData()
        self._translate()

    def folder_paths(self):
        return [self.folders.item(i).text() for i in range(self.folders.count())]

    def options(self):
        return Options(self.checkboxes['normalize'].isChecked(), self.checkboxes['dedup'].isChecked(),
                       self.checkboxes['transliterate'].isChecked(), self.checkboxes['save_log'].isChecked(),
                       self.log_path.text())

    def signature(self):
        return (tuple(self.folder_paths()), self.options())

    def _busy(self):
        return self.runner is not None

    def _invalidate_preview(self):
        self.preview_signature = None
        if not self._busy():
            self._set_status('ready')
        self._refresh_controls()

    def _refresh_controls(self):
        # Signals may arrive during widget construction.
        if not hasattr(self, 'apply_button'):
            return
        busy = self._busy()
        self.preview_button.setEnabled(not busy and self.folders.count() > 0)
        self.apply_button.setEnabled(not busy and self.preview_signature == self.signature())
        self.cancel_button.setEnabled(busy and not (self.cancel_file and self.cancel_file.exists()))
        self.add_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and bool(self.folders.selectedItems()))
        self.folders.setEnabled(not busy)
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(not busy)
        save_log = self.checkboxes['save_log'].isChecked()
        self.log_path.setEnabled(not busy and save_log)
        self.log_browse.setEnabled(not busy and save_log)
        self.open_log_button.setEnabled(self.last_log is not None and self.last_log.is_file())
        self.clear_button.setEnabled(not busy)

    def _set_status(self, key):
        self.status_key = key
        self.status.setText(self.t(key))

    def add_folder_path(self, value):
        try:
            paths = unique_folders(self.folder_paths() + [value])
        except ValueError as exc:
            QMessageBox.warning(self, self.t('invalid'), str(exc))
            return
        self.folders.clear()
        self.folders.addItems([str(p) for p in paths])
        self._invalidate_preview()

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.t('select_folder'))
        if folder:
            self.add_folder_path(folder)

    def _remove_folders(self):
        for item in self.folders.selectedItems():
            self.folders.takeItem(self.folders.row(item))
        self._invalidate_preview()

    def _browse_log(self):
        name, _ = QFileDialog.getSaveFileName(self, self.t('choose_log'), self.log_path.text() or 'font_renamer.log', 'Log (*.log);;Text (*.txt)')
        if name:
            self.log_path.setText(name)

    def _confirm_apply(self):
        if self.preview_signature != self.signature():
            return
        if QMessageBox.question(self, self.t('confirm_title'), self.t('confirm')) == QMessageBox.StandardButton.Yes:
            self.start_run(True)

    def start_run(self, apply=False):
        if self._busy() or (apply and self.preview_signature != self.signature()):
            return
        temp = tempfile.TemporaryDirectory(prefix='font-renamer-gui-')
        cancel_file = Path(temp.name) / 'cancel.flag'
        try:
            args, log = build_arguments(self.folder_paths(), self.options(), apply, cancel_file)
            command = worker_command() + args
        except Exception as exc:
            temp.cleanup()
            QMessageBox.warning(self, self.t('invalid'), str(exc))
            return
        self.cancel_temp = temp
        self.cancel_file = cancel_file
        self.last_log = log
        self.running_apply = apply
        self.run_signature = self.signature()
        self.result = None
        self.preview_signature = None
        self.output.clear()
        self.progress.setRange(0, 0)
        self._set_status('applying' if apply else 'previewing')
        self.runner = EngineRunner(command, self.folder_paths()[0], self)
        self.runner.output.connect(self._append_output)
        self.runner.completed.connect(self._store_result)
        self.runner.finished.connect(self._finished)
        self._refresh_controls()
        self.runner.start()

    def _append_output(self, text):
        scrollbar = self.output.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 5
        self.output.appendPlainText(text)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        for match in re.finditer(r'(\d+) changes, (\d+) byte-identical duplicates, (\d+) errors\.', text):
            self.summary = {'changes':match[1], 'duplicates':match[2], 'errors':match[3]}

    def _store_result(self, code):
        self.result = code

    def _finished(self):
        runner = self.runner
        self.runner = None
        runner.deleteLater()
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        code = self.result if self.result is not None else 2
        if code == 130:
            key = 'cancelled'
        elif code not in (0, 1):
            key = 'failed'
        elif self.running_apply:
            key = 'done' if code == 0 else 'issues'
        else:
            key = 'preview_done' if code == 0 else 'preview_issues'
            self.preview_signature = self.run_signature
        self._set_status(key)
        if hasattr(self, 'summary'):
            self.status.setText(self.status.text() + '  ' + self.t('summary').format(**self.summary))
            del self.summary
        self.cancel_temp.cleanup()
        self.cancel_temp = self.cancel_file = None
        self._refresh_controls()
        if self.close_pending:
            self.close()

    def _cancel(self):
        if self._busy() and self.cancel_file is not None:
            try:
                self.cancel_file.touch()
            except OSError as exc:
                QMessageBox.warning(self, self.t('invalid'), str(exc))
                return
            self._set_status('cancelling')
            self._refresh_controls()

    def _open_log(self):
        if self.last_log is not None and self.last_log.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_log)))

    def _clear_output(self):
        self.output.clear()

    def closeEvent(self, event):
        if self._busy():
            if QMessageBox.question(self, self.t('close_title'), self.t('close')) == QMessageBox.StandardButton.Yes:
                self.close_pending = True
                self._cancel()
            event.ignore()
            return
        if self.persist:
            self.settings.setValue('language', self.language)
            self.settings.setValue('folders', self.folder_paths())
            for key, checkbox in self.checkboxes.items():
                self.settings.setValue(key, checkbox.isChecked())
            self.settings.setValue('log_path', self.log_path.text())
            self.settings.sync()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Font Renamer')
    app.setStyle('Fusion')
    # Packaging diagnostics run only a preview on a caller-supplied test folder.
    diagnostic = len(sys.argv) == 4 and sys.argv[1] == '--preview-test'
    window = MainWindow(persist=not diagnostic)
    window.show()
    if diagnostic:
        import json
        from PySide6.QtCore import QTimer
        folder, report = Path(sys.argv[2]), Path(sys.argv[3])
        window.folders.addItem(str(folder))
        def start():
            window.start_run(False)
            def finish():
                report.write_text(json.dumps({'preview_ready': window.preview_signature is not None,
                    'output': window.output.toPlainText()}, ensure_ascii=False), encoding='utf-8')
                app.quit()
            window.runner.finished.connect(finish)
        QTimer.singleShot(0, start)
        QTimer.singleShot(60000, lambda: app.exit(2))
    return app.exec()
