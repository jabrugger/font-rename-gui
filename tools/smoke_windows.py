"""Exercise the actual packaged GUI and worker using disposable generated fonts."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.test_gui import make_font


def main():
    package = ROOT/'dist'/'FontRenamer'
    worker = package/'worker'/'FontRenamerWorker.exe'
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)/'Fonts with spaces 字体'
        folder.mkdir()
        make_font(folder/' source.ttf')
        shutil.copy2(folder/' source.ttf', folder/'duplicate.ttf')
        before = {p.name:p.read_bytes() for p in folder.iterdir()}
        report = Path(temporary)/'gui-report.json'
        subprocess.run([str(package/'FontRenamer.exe'), '--preview-test', str(folder), str(report)],
            env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), check=True, timeout=75)
        result = json.loads(report.read_text(encoding='utf-8'))
        assert result['preview_ready'], result
        assert 'Test Regular.ttf' in result['output'], result
        assert all((folder/name).read_bytes() == data for name,data in before.items())
        applied = subprocess.run([str(worker), str(folder), '--normalize-internal', '--apply', '--log'],
            cwd=folder, capture_output=True, encoding='utf-8', check=True, timeout=60)
        assert 'Test Regular.ttf' in applied.stdout, applied.stdout
        assert len(list(folder.glob('*.ttf'))) == 1
        assert list(folder.glob('*.log'))
    print('Packaged GUI preview, Unicode paths, worker application, duplicate removal and logs: OK')


if __name__ == '__main__':
    main()
