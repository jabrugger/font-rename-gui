"""Render a reproducible demo with fictional folders, without processing fonts."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from font_rename_gui.app import MainWindow

app = QApplication([])
for name in ('segoeui.ttf', 'consola.ttf'):
    QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/name))
app.setStyle('Fusion')
window = MainWindow(persist=False)
window.folders.addItems([r'C:\Fonts\Serif', r'C:\Fonts\Sans Serif', r'C:\Fonts\Symbols'])
window._append_output("PREVIEW: no files will be changed.\n\nRENAME:\n  CURRENT: ' antique serif.ttf'\n  NEW: 'Antique Serif Regular.ttf'\n  FOLDER: C:\\Fonts\\Serif\n\nINTERNAL:\n  FILE: Antique Serif Regular.ttf\n  NAME ID 1:\n    CURRENT: ' Antique Serif '\n    NEW: 'Antique Serif'\n\n3 changes, 0 byte-identical duplicates, 0 errors.")
window.preview_signature = window.signature()
window._set_status('preview_done')
window._refresh_controls()
window.show()
app.processEvents()
target = Path(sys.argv[1]).absolute()
target.parent.mkdir(parents=True, exist_ok=True)
if not window.grab().save(str(target)):
    raise SystemExit('Screenshot could not be saved')
window.close()
print(target)
