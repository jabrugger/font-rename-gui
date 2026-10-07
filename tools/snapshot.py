"""Render a reproducible demo with fictional folders, without processing fonts."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from font_rename_neo_gui.app import MainWindow

app = QApplication([])
for name in ('segoeui.ttf', 'consola.ttf'):
    QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/name))
app.setStyle('Fusion')
window = MainWindow(persist=False)
window.add_folder_path(str(Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'))
window._append_output("PREVIEW: no files will be changed.\n\nRENAME:\n  CURRENT: ' antique serif.ttf'\n  NEW: 'Antique Serif Regular.ttf'\n  FOLDER: C:\\Fonts\\Serif\n\nINTERNAL:\n  FILE: Antique Serif Regular.ttf\n  FOLDER: C:\\Fonts\\Serif\n  NAME ID 1:\n    CURRENT: ' Antique Serif '\n    NEW: 'Antique Serif'\n\n3 changes, 0 byte-identical duplicates, 0 errors.")
window._append_output("RENAME:\n  CURRENT: 'YangJae.ttf'\n  NEW: 'YangJae [original].ttf'\n  FOLDER: C:\\Fonts\\Symbolica\nDUPLICATE:\n  CURRENT: Antique Serif copy.ttf\n  FOLDER: C:\\Fonts\\Serif\n  KEEP: C:\\Fonts\\Serif\\Antique Serif Regular.ttf\nERROR (kept): C:\\Fonts\\broken.ttf: Invalid font header\n")
window.preview_view.set_language('es')
window.preview_view.finish()
window.view_stack.setCurrentIndex(1)
window.preview_view.begin_apply()
for row in window.preview_view.rows:
    if row['status']!='error':
        row['status']='done'
window.preview_view.refresh()
window.preview_view.table.selectRow(0)
window.preview_signature = None
window._set_status('issues')
window._refresh_controls()
window.show()
app.processEvents()
target = Path(sys.argv[1]).absolute()
target.parent.mkdir(parents=True, exist_ok=True)
if not window.grab().save(str(target)):
    raise SystemExit('Screenshot could not be saved')
window.close()
print(target)
