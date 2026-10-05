"""Build a portable directory with a separate, console-capable engine."""
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def build(name, script, extra):
    # Unrelated tools on PATH can supply incompatible DLLs with the same name
    # (for example Poppler's ICU instead of Windows' ICU used by Qt).
    windows = Path(os.environ.get('WINDIR', 'C:/Windows'))
    environment = dict(os.environ)
    environment['PATH'] = os.pathsep.join(str(p) for p in (
        Path(sys.executable).parent, Path(sys.base_prefix),
        Path(sys.base_prefix)/'DLLs', windows/'System32', windows))
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--onedir',
                    '--name', name, '--distpath', str(DIST),
                    '--workpath', str(ROOT/'build'/name), '--specpath', str(ROOT/'build'),
                    *extra, str(ROOT/script)], cwd=ROOT, env=environment, check=True)


def main():
    if sys.platform != 'win32':
        raise SystemExit('The Windows package must be built on Windows.')
    build('FontRenamer', 'launch_gui.py', ['--windowed', '--copy-metadata', 'font-rename-fm'])
    build('FontRenamerWorker', 'launch_worker.py', ['--console', '--collect-data', 'anyascii',
          '--collect-submodules', 'fontTools.ttLib.tables', '--hidden-import', 'fontTools.cffLib'])
    app = DIST/'FontRenamer'
    worker = app/'worker'
    shutil.copytree(DIST/'FontRenamerWorker', worker, dirs_exist_ok=True)
    shutil.copy2(ROOT/'LICENSE', app/'LICENSE')
    shutil.copy2(ROOT/'README.md', app/'README.md')
    shutil.copy2(ROOT/'THIRD_PARTY_NOTICES.md', app/'THIRD_PARTY_NOTICES.md')
    notices = app/'licenses'
    notices.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'third_party_licenses', notices/'upstream', dirs_exist_ok=True)
    inventory = {}
    for name in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6',
                 'font-rename-fm', 'fonttools', 'anyascii', 'faust-cchardet', 'pyinstaller'):
        dist = importlib.metadata.distribution(name)
        inventory[name] = {'version':dist.version, 'license':dist.metadata.get('License-Expression', dist.metadata.get('License', 'See included license texts'))}
        for entry in dist.files or []:
            if any(token in entry.name.casefold() for token in ('license', 'licence', 'copying')) and entry.suffix.lower() in {'.txt', '.md', '', '.rst'}:
                source = Path(dist.locate_file(entry))
                if source.is_file():
                    target = notices/name/Path(str(entry)).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license, notices/'CPython-LICENSE.txt')
    (notices/'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    archive = shutil.make_archive(str(DIST/'FontRenamerGUI-0.1.0-windows-x64'), 'zip', DIST, 'FontRenamer')
    print(archive)


if __name__ == '__main__':
    main()
