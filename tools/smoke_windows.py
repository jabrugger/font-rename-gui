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
from font_rename_fm.rename import FileDates
from fontTools.ttLib import TTFont


def main():
    package = ROOT/'dist'/'FontRenamer'
    worker = package/'worker'/'FontRenamerWorker.exe'
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)/'Fonts with spaces 字体'
        folder.mkdir()
        make_font(folder/' source.ttf')
        with TTFont(folder/' source.ttf', recalcTimestamp=False) as font:
            for record in font['name'].names:
                if record.nameID in (1,4):
                    record.string = (' '+record.toUnicode()+' ').encode(record.getEncoding())
            font.save(folder/' source.ttf')
        shutil.copy2(folder/' source.ttf', folder/'duplicate.ttf')
        dates=FileDates(946684800123456700,978307200765432100,
                        915148800345678900 if os.name=='nt' else None)
        for path in folder.glob('*.ttf'):
            dates.restore(path)
        expected=FileDates.capture(folder/' source.ttf')
        before = {p.name:p.read_bytes() for p in folder.iterdir()}
        nested = folder/'Nested'
        nested.mkdir()
        shutil.copy2(folder/' source.ttf', nested/'nested.ttf')
        report = Path(temporary)/'gui-report.json'
        subprocess.run([str(package/'FontRenamer.exe'), '--preview-test', str(folder), str(report)],
            env=dict(os.environ, QT_QPA_PLATFORM='offscreen'), check=True, timeout=75)
        result = json.loads(report.read_text(encoding='utf-8'))
        assert result['preview_ready'], result
        assert 'Test Regular.ttf' in result['output'], result
        assert all((folder/name).read_bytes() == data for name,data in before.items())
        assert list((folder/'BAK').glob('*.log'))
        nested_log = next((nested/'BAK').glob('*.log'))
        previous_nested_log = nested_log.read_bytes()
        applied = subprocess.run([str(worker), str(folder), '--normalize-internal', '--apply',
            '--log-per-folder', '--no-recursive'],
            cwd=folder, capture_output=True, encoding='utf-8', check=True, timeout=60)
        assert 'Test Regular.ttf' in applied.stdout, applied.stdout
        assert len(list(folder.glob('*.ttf'))) == 1
        assert list((folder/'BAK').glob('*.log'))
        assert (nested/'nested.ttf').is_file()
        assert nested_log.read_bytes() == previous_nested_log
        for path in (folder/'Test Regular.ttf',folder/'BAK'/'Test Regular.ttf.original.bak'):
            actual=FileDates.capture(path)
            assert actual.modified_ns==expected.modified_ns,(path,actual,expected)
            assert actual.created_ns==expected.created_ns,(path,actual,expected)
    print('Packaged GUI, per-folder logs, recursion, normalization and original creation/modification dates: OK')


if __name__ == '__main__':
    main()
