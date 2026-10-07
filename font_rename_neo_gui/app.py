import re
import sys
import tempfile
from pathlib import Path
from importlib.metadata import version

from PySide6.QtCore import QLocale, QSettings, Qt, QUrl, QTranslator, QLibraryInfo
from PySide6.QtGui import QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QStackedWidget, QStyle, QPushButton, QSplitter, QVBoxLayout, QWidget)

from . import __version__
from .model import Options, build_arguments, unique_folders, worker_command, default_log_directory
from .runner import EngineRunner
from .preview import PreviewWidget

TEXT = {
 'es': {
  'subtitle':'Ordená tu colección de fuentes.', 'folders':'Carpeta',
  'folders_hint':'Elegí una carpeta. Los respaldos BAK quedan excluidos.',
  'recursive':'Incluir subcarpetas',
  'skip_preview':'Aplicar sin vista previa',
  'skip_preview_tip':'Permite aplicar directamente a la carpeta elegida. Siempre solicita confirmación antes de modificar archivos.',
  'add':'Elegir carpeta', 'remove':'Quitar', 'options':'Opciones',
  'normalize':'Limpiar nombres internos', 'normalize_tip':'Conserva el original en una subcarpeta BAK.',
  'dedup':'Eliminar duplicados idénticos', 'dedup_tip':'Solo elimina copias con exactamente los mismos bytes.',
  'transliterate':'Transliterar nombres', 'transliterate_tip':'Agrega un nombre latino y conserva el original entre corchetes.',
  'transliterate_help':'Solo se aplica a nombres en otros alfabetos (chino, árabe, coreano, etc.). Agrega una transliteración latina y conserva el nombre original entre corchetes; los nombres latinos no se transliteran.',
  'save_log':'Guardar log completo', 'log_hint':'Automático: BAK de cada carpeta procesada',
  'clear_tip':'Borra únicamente el texto de Actividad. No borra los archivos de log.',
  'browse_log':'Elegir carpeta de logs', 'output':'Actividad', 'clear':'Limpiar pantalla',
  'output_hint':'La pantalla conserva las últimas 3.000 líneas. El log guarda la salida completa.',
  'empty':'Agregá una carpeta y revisá la vista previa antes de aplicar cambios.',
  'preview':'Vista previa', 'apply':'Aplicar cambios', 'cancel':'Detener proceso', 'open_log':'Abrir log',
  'ready':'Listo para revisar', 'previewing':'Generando vista previa…', 'applying':'Aplicando cambios…',
  'cancelling':'Cancelando al terminar la fuente en curso…', 'cancelled':'Cancelado. Los cambios terminados se conservan.',
  'preview_done':'Vista previa terminada. Podés aplicar los cambios.', 'preview_issues':'Vista previa terminada con errores. Revisá el log.',
  'done':'Ejecución terminada.', 'issues':'Ejecución terminada con errores. Revisá el log.', 'failed':'No se pudo ejecutar el motor.',
  'confirm_title':'Confirmar ejecución',
  'confirm':'¿Está seguro de ejecutar el proceso sobre la carpeta seleccionada?\n\nSegún las opciones elegidas, el proceso puede renombrar archivos, modificar nombres internos y eliminar duplicados idénticos.\nLos respaldos BAK cubren cambios internos; el borrado de duplicados no tiene deshacer.',
  'invalid':'Revisá la selección', 'close_title':'Ejecución en curso',
  'close':'Para cerrar, se cancelará entre fuentes. Los cambios ya terminados se conservarán. ¿Solicitar la cancelación?',
  'summary':'{changes} cambios · {duplicates} duplicados · {errors} errores',
  'select_folder':'Elegir carpeta de fuentes', 'choose_log':'Carpeta de logs', 'idle':'VISTA PREVIA PRIMERO',
 },
 'en': {
  'subtitle':'Bring order to your font collection.', 'folders':'Folder',
  'folders_hint':'Choose one folder. BAK backups are excluded.',
  'recursive':'Include subfolders',
  'skip_preview':'Apply without preview',
  'skip_preview_tip':'Allows applying directly to the selected folder. Always asks for confirmation before modifying files.',
  'add':'Choose folder', 'remove':'Remove', 'options':'Options',
  'normalize':'Clean internal names', 'normalize_tip':'Keeps the original in a BAK subfolder.',
  'dedup':'Remove identical duplicates', 'dedup_tip':'Only removes copies with exactly the same bytes.',
  'transliterate':'Transliterate names', 'transliterate_tip':'Adds a Latin name and keeps the original in brackets.',
  'transliterate_help':'Only applies to names in other writing systems (Chinese, Arabic, Korean, etc.). Adds a Latin transliteration and keeps the original name in brackets; Latin names are not transliterated.',
  'save_log':'Save complete log', 'log_hint':'Automatic: logs beside the EXE',
  'clear_tip':'Clears only the Activity display. Does not delete log files.',
  'browse_log':'Choose log folder', 'output':'Activity', 'clear':'Clear screen',
  'output_hint':'The screen keeps the latest 3,000 lines. The log keeps the complete output.',
  'empty':'Add a folder and review the preview before applying changes.',
  'preview':'Preview', 'apply':'Apply changes', 'cancel':'Stop process', 'open_log':'Open log',
  'ready':'Ready to preview', 'previewing':'Generating preview…', 'applying':'Applying changes…',
  'cancelling':'Cancelling after the current font…', 'cancelled':'Cancelled. Completed changes are retained.',
  'preview_done':'Preview finished. You can apply changes.', 'preview_issues':'Preview finished with errors. Review the log.',
  'done':'Run finished.', 'issues':'Run finished with errors. Review the log.', 'failed':'The engine could not be started.',
  'confirm_title':'Confirm execution',
  'confirm':'Are you sure you want to run the process on the selected folder?\n\nDepending on the selected options, the process may rename files, modify internal names and remove identical duplicates.\nBAK backups cover internal changes; duplicate removal has no undo.',
  'invalid':'Check your selection', 'close_title':'Run in progress',
  'close':'Closing requests cancellation between fonts. Completed changes will be retained. Request cancellation?',
  'summary':'{changes} changes · {duplicates} duplicates · {errors} errors',
  'select_folder':'Choose a font folder', 'choose_log':'Log folder', 'idle':'PREVIEW FIRST',
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
QCheckBox::indicator:unchecked { border:1px solid #a2acba; border-radius:3px; background:#202730; }
QCheckBox::indicator:checked { image:url("__CHECK_IMAGE__"); }
QCheckBox:hover { color:#f0cc94; }
QCheckBox::indicator:unchecked:hover { border:2px solid #e2b97b; }
QCheckBox:disabled { color:#78828f; }
QCheckBox::indicator:disabled { border:1px solid #465263; border-radius:3px; background:#252d38; }
QComboBox { background:#252e3a; padding:6px 12px; border:1px solid #465263; border-radius:5px; }
QComboBox QAbstractItemView { background:#252e3a; selection-background-color:#465263; }
QProgressBar { background:#252e3a; border:0; border-radius:3px; max-height:5px; }
QProgressBar::chunk { background:#e2b97b; }
QScrollBar:vertical { width:12px; background:#171c23; }
QScrollBar::handle:vertical { background:#465263; border-radius:5px; min-height:20px; }
QSplitter::handle { background:#394350; border-top:1px solid #647083; border-bottom:1px solid #647083; }
QSplitter::handle:hover { background:#e2b97b; }
QLabel#detailCaption { color:#e2b97b; font-weight:600; padding:5px 0; }
QTableView { background:#171c23; alternate-background-color:#202730; color:#e6e9ed; gridline-color:#323b48; selection-background-color:#394758; selection-color:#ffffff; border:1px solid #394350; }
QHeaderView::section { background:#252e3a; color:#e6e9ed; padding:8px; border:0; border-bottom:1px solid #465263; }
QTabWidget::pane { border:1px solid #323b48; }
QTabBar::tab { background:#202730; padding:10px 18px; border:1px solid #323b48; }
QTabBar::tab:selected { background:#303a47; color:#e2b97b; }
'''


class MainWindow(QMainWindow):
    def __init__(self, persist=True):
        super().__init__()
        self.persist = persist
        self.settings = QSettings('jabrugger', 'FontRenameNeoGUI')
        system_language = 'es' if QLocale.system().language() == QLocale.Language.Spanish else 'en'
        self.language = self.settings.value('language', system_language) if persist else 'es'
        if self.language not in TEXT:
            self.language = system_language
        app = QApplication.instance()
        if not hasattr(app, '_font_rename_neo_translator'):
            app._font_rename_neo_translator = QTranslator(app)
        self.qt_translator = app._font_rename_neo_translator
        self.runner = None
        self.cancel_temp = None
        self.cancel_file = None
        self.last_log = None
        self.preview_signature = None
        self.running_apply = False
        self.close_pending = False
        self.result = None
        self.setWindowTitle('Font Rename Neo')
        self.setWindowIcon(QIcon(str(Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))/'assets'/'font-rename-neo.ico')))
        self.resize(1120, 940)
        self.setMinimumSize(940, 700)
        assets = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))/'assets'
        self.setStyleSheet(STYLE.replace('__CHECK_IMAGE__',(assets/'checkbox-checked.svg').as_posix()))
        self._build()
        self._translate()
        if persist:
            for folder in self.settings.value('folders', [], type=list):
                if Path(folder).is_dir():
                    self.folders.addItem(folder)
                    break
            self.recursive.setChecked(self.settings.value('recursive', True, type=bool))
            for key, checkbox in self.checkboxes.items():
                checkbox.setChecked(self.settings.value(key, True, type=bool))
            self.log_path.setText(self.settings.value('log_directory', ''))
        self.folder_line.setText(self.folder_paths()[0] if self.folder_paths() else '')
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
        title = QLabel('Font Rename Neo')
        title.setObjectName('title')
        heading.addWidget(title)
        heading.addWidget(self._label('subtitle'))
        header.addLayout(heading)
        header.addStretch()
        self.language_picker = QComboBox()
        self.language_picker.addItem('Español', 'es')
        self.language_picker.addItem('English', 'en')
        self.language_picker.setCurrentIndex(0 if self.language == 'es' else 1)
        self.language_picker.currentIndexChanged.connect(self._change_language)
        header.addWidget(self.language_picker)
        layout.addLayout(header)
        self.folders = QListWidget()
        self.folders.hide()  # Retained as the validated selection store, never displayed.
        folder_row = QHBoxLayout()
        folder_row.addWidget(self._label('folders',False))
        self.folder_line = QLineEdit()
        self.folder_line.setReadOnly(True)
        folder_row.addWidget(self.folder_line,1)
        self.add_button = self._button('add',self._add_folder)
        folder_row.addWidget(self.add_button)
        self.remove_button = self._button('remove',self._remove_folders)
        self.remove_button.hide()
        self.recursive = QCheckBox()
        self.recursive.setChecked(True)
        self.recursive.toggled.connect(self._invalidate_preview)
        self.labels.append((self.recursive,'recursive'))
        folder_row.addWidget(self.recursive)
        layout.addLayout(folder_row)
        option_row = QHBoxLayout()
        self.checkboxes = {}
        for key in ['normalize','dedup','transliterate','save_log']:
            checkbox=QCheckBox()
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._invalidate_preview)
            self.labels.append((checkbox,key))
            self.checkboxes[key]=checkbox
            option_row.addWidget(checkbox)
        self.skip_preview=QCheckBox()
        self.skip_preview.setChecked(False)
        self.skip_preview.toggled.connect(self._invalidate_preview)
        self.labels.append((self.skip_preview,'skip_preview'))
        option_row.addWidget(self.skip_preview)
        option_row.addStretch()
        self.log_settings=QPushButton('Logs\u2026')
        option_row.addWidget(self.log_settings)
        layout.addLayout(option_row)
        self.log_panel=QWidget()
        log_row=QHBoxLayout(self.log_panel)
        log_row.setContentsMargins(0,0,0,0)
        self.log_path=QLineEdit()
        self.log_path.textChanged.connect(self._invalidate_preview)
        self.log_browse=QPushButton('\u2026')
        self.log_browse.clicked.connect(self._browse_log)
        log_row.addWidget(self.log_path,1)
        log_row.addWidget(self.log_browse)
        layout.addWidget(self.log_panel)
        self.log_panel.hide()
        self.log_settings.clicked.connect(lambda:self.log_panel.setVisible(not self.log_panel.isVisible()))
        self.view_stack=QStackedWidget()
        activity_panel,al=self._panel('output')
        toolbar=QHBoxLayout()
        toolbar.addWidget(self._label('output_hint'))
        toolbar.addStretch()
        self.clear_button=self._button('clear',self._clear_output)
        toolbar.addWidget(self.clear_button)
        al.addLayout(toolbar)
        self.output=QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(3000)
        self.output.setFont(QFont('Consolas',10))
        al.addWidget(self.output,1)
        self.view_stack.addWidget(activity_panel)
        self.preview_view=PreviewWidget()
        self.view_stack.addWidget(self.preview_view)
        layout.addWidget(self.view_stack,1)
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
        self.preview_button = self._button('preview', self._preview_action)
        self.apply_button = self._button('apply', self._confirm_apply)
        self.apply_button.setObjectName('primary')
        self.cancel_button.hide()
        for button in (self.preview_button, self.apply_button):
            actions.addWidget(button)
        layout.addLayout(actions)
        try:
            engine_version = version('font-rename-neo')
        except Exception:
            engine_version = '?'
        self.footer = QLabel(
            f'<a href="https://github.com/jabrugger/font-rename-neo-gui" style="color:#a2acba">'
            f'GUI {__version__}</a> &nbsp; &middot; &nbsp; '
            f'<a href="https://github.com/jabrugger/font-rename-neo" style="color:#a2acba">'
            f'font-rename-neo {engine_version}</a> &nbsp; &middot; &nbsp; MIT')
        self.footer.setObjectName('muted')
        self.footer.setTextFormat(Qt.TextFormat.RichText)
        self.footer.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse |
                                           Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
        self.footer.setOpenExternalLinks(True)
        layout.addWidget(self.footer)

    def _translate(self):
        app = QApplication.instance()
        app.removeTranslator(self.qt_translator)
        if self.language == 'es':
            translations = Path(sys._MEIPASS)/'translations' if getattr(sys, 'frozen', False) else Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
            if self.qt_translator.load(str(translations/'qtbase_es.qm')):
                app.installTranslator(self.qt_translator)
        self.language_picker.setItemText(0, 'Espa\u00f1ol' if self.language == 'es' else 'Spanish')
        self.language_picker.setItemText(1, 'Ingl\u00e9s' if self.language == 'es' else 'English')
        self.checkboxes['normalize'].setToolTip(self.t('normalize_tip'))
        self.checkboxes['dedup'].setToolTip(self.t('dedup_tip'))
        self.checkboxes['transliterate'].setToolTip(self.t('transliterate_help'))
        self.clear_button.setToolTip(self.t('clear_tip'))
        self.skip_preview.setToolTip(self.t('skip_preview_tip'))
        self.cancel_button.setToolTip('Detiene entre archivos. Conserva los cambios ya realizados; no deshace operaciones.' if self.language=='es' else 'Stops between files. Completed changes remain; operations are not undone.')
        for widget, key in self.labels:
            widget.setText(self.t(key))
        for button, key in self.buttons:
            button.setText(self.t(key))
        self.preview_view.set_language(self.language)
        self.log_path.setPlaceholderText(str(default_log_directory()))
        self.log_path.setToolTip(self.t('log_hint'))
        self.log_browse.setToolTip(self.t('browse_log'))
        self.output.setPlaceholderText(self.t('empty'))
        self.status.setText(self.t(self.status_key))

    def _change_language(self):
        self.language = self.language_picker.currentData()
        self._translate()
        self._refresh_controls()

    def folder_paths(self):
        return [self.folders.item(i).text() for i in range(self.folders.count())]

    def options(self):
        return Options(self.checkboxes['normalize'].isChecked(), self.checkboxes['dedup'].isChecked(),
                       self.checkboxes['transliterate'].isChecked(), self.checkboxes['save_log'].isChecked(),
                       self.log_path.text(), self.recursive.isChecked())

    def signature(self):
        return (tuple(self.folder_paths()), self.options(), self.skip_preview.isChecked())

    def _busy(self):
        return self.runner is not None

    def _invalidate_preview(self):
        self.preview_signature = None
        if hasattr(self,'folder_line'):
            self.folder_line.setText(self.folder_paths()[0] if self.folder_paths() else '')
        if hasattr(self,'preview_view'):
            self.preview_view.stale()
        if not self._busy():
            self._set_status('ready')
        self._refresh_controls()

    def _refresh_controls(self):
        # Signals may arrive during widget construction.
        if not hasattr(self, 'apply_button'):
            return
        busy = self._busy()
        stopping = bool(self.cancel_file and self.cancel_file.exists())
        self.preview_button.setEnabled((not busy and self.folders.count()>0) or (busy and not self.running_apply and not stopping))
        self.apply_button.setEnabled((not busy and self.folders.count()>0 and
            (self.skip_preview.isChecked() or self.preview_signature == self.signature())) or
            (busy and self.running_apply and not stopping))
        stop_tip='Detiene entre archivos. Conserva los cambios ya realizados; no deshace operaciones.' if self.language=='es' else 'Stops between files. Completed changes remain; operations are not undone.'
        for button,key,active in [(self.preview_button,'preview',busy and not self.running_apply),(self.apply_button,'apply',busy and self.running_apply)]:
            button.setText(('Detener' if self.language=='es' else 'Stop') if active else self.t(key))
            button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop if active else QStyle.StandardPixmap.SP_MediaPlay))
            button.setToolTip(stop_tip if active else self.t(key))
        self.cancel_button.setEnabled(busy and not (self.cancel_file and self.cancel_file.exists()))
        self.add_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and bool(self.folders.selectedItems()))
        self.folders.setEnabled(not busy)
        self.recursive.setEnabled(not busy)
        self.skip_preview.setEnabled(not busy)
        for checkbox in self.checkboxes.values():
            checkbox.setEnabled(not busy)
        save_log = self.checkboxes['save_log'].isChecked()
        self.log_path.setEnabled(not busy and save_log)
        self.log_browse.setEnabled(not busy and save_log)
        self.open_log_button.setEnabled(self.last_log is not None and self.last_log.is_file())
        self.clear_button.setEnabled(True)

    def _set_status(self, key):
        self.status_key = key
        self.status.setText(self.t(key))

    def add_folder_path(self, value):
        try:
            paths = unique_folders([value])
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
        name = QFileDialog.getExistingDirectory(self, self.t('choose_log'), self.log_path.text() or str(default_log_directory()))
        if name:
            self.log_path.setText(name)

    def _preview_action(self):
        if self._busy():
            if not self.running_apply: self._cancel()
        else:
            self.start_run(False)

    def _confirm_apply(self):
        if self._busy():
            if self.running_apply: self._cancel()
            return
        if not self.skip_preview.isChecked() and self.preview_signature != self.signature():
            return
        if QMessageBox.question(self, self.t('confirm_title'), self.t('confirm'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.start_run(True)

    def start_run(self, apply=False):
        if self._busy() or (apply and not self.skip_preview.isChecked() and self.preview_signature != self.signature()):
            return
        had_preview = self.preview_signature == self.signature()
        temp = tempfile.TemporaryDirectory(prefix='font-rename-neo-gui-')
        cancel_file = Path(temp.name) / 'cancel.flag'
        try:
            args, log = build_arguments(self.folder_paths(), self.options(), apply, cancel_file)
            command = worker_command() + args + ['--gui-events']
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
        if not apply or not had_preview:
            self.preview_view.reset()
            self.preview_view.set_language(self.language)
        if apply:
            self.preview_view.begin_apply()
        self.view_stack.setCurrentIndex(1 if apply else 0)
        self.progress.setRange(0, 0)
        self._set_status('applying' if apply else 'previewing')
        self.runner = EngineRunner(command, self.folder_paths()[0], self)
        self.runner.output.connect(self._append_output)
        self.runner.completed.connect(self._store_result)
        self.runner.finished.connect(self._finished)
        self._refresh_controls()
        self.runner.start()

    def _append_output(self, text):
        self.preview_view.consume(text)
        for line in text.splitlines():
            if line.startswith('LOG: '):
                self.last_log = Path(line[5:])
        scrollbar = self.output.verticalScrollBar()
        at_bottom = scrollbar.value() >= scrollbar.maximum() - 5
        visible='\n'.join(line for line in text.splitlines() if not line.startswith('GUI_EVENT: '))
        if visible:
            self.output.appendPlainText(visible)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        for match in re.finditer(r'(\d+) changes, (\d+) byte-identical duplicates, (\d+) errors\.', text):
            self.summary = {'changes':match[1], 'duplicates':match[2], 'errors':match[3]}

    def _store_result(self, code):
        self.result = code

    def _finished(self):
        if self.running_apply:
            self.preview_view.finish_apply()
        else:
            self.preview_view.finish()
            if self.preview_view.proxy.rowCount():
                self.preview_view.table.selectRow(0)
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
        self.view_stack.setCurrentIndex(1)
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
        self.output.setPlaceholderText('')

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
            self.settings.setValue('recursive', self.recursive.isChecked())
            for key, checkbox in self.checkboxes.items():
                self.settings.setValue(key, checkbox.isChecked())
            self.settings.setValue('log_directory', self.log_path.text())
            self.settings.sync()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Font Rename Neo')
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
                dialog = QMessageBox(window)
                dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                yes_label = dialog.button(QMessageBox.StandardButton.Yes).text().replace('&', '')
                report.write_text(json.dumps({'yes_label': yes_label, 'preview_ready': window.preview_signature is not None,
                    'output': window.output.toPlainText(), 'log': str(window.last_log), 'preview_rows': len(window.preview_view.rows), 'preview_visible':window.view_stack.currentIndex()==1}, ensure_ascii=False), encoding='utf-8')
                app.quit()
            window.runner.finished.connect(finish)
        QTimer.singleShot(0, start)
        QTimer.singleShot(60000, lambda: app.exit(2))
    return app.exec()
