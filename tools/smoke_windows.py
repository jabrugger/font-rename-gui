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
        folder = Path(temporary)/'Fonts with spaces å­—ä½“'
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
        assert result['preview_rows'] >= 2, result
        assert result['preview_visible'], result
        assert result['yes_label'] == 'S\u00ed', result
        assert (package/'_internal'/'translations'/'qtbase_es.qm').is_file()
        assert 'Test Regular.ttf' in result['output'], result
        assert all((folder/name).read_bytes() == data for name,data in before.items())
        log=Path(result['log'])
        assert log.parent == package/'logs'
        assert log.is_file()
        assert not (folder/'BAK').exists()
        assert not (nested/'BAK').exists()
        applied = subprocess.run([str(worker), str(folder), '--normalize-internal', '--apply',
            '--log',str(log),'--no-recursive','--gui-events'],
            cwd=folder, capture_output=True, encoding='utf-8', check=True, timeout=60)
        assert 'Test Regular.ttf' in applied.stdout, applied.stdout
        events=[json.loads(line[11:]) for line in applied.stdout.splitlines() if line.startswith('GUI_EVENT: ')]
        assert any(e['phase']=='file' and e['status']=='done' for e in events),events
        assert any(e['phase']=='internal' and e['status']=='done' for e in events),events
        assert len(list(folder.glob('*.ttf'))) == 1
        assert not list((folder/'BAK').glob('*.log'))
        assert (nested/'nested.ttf').is_file()
        assert not (nested/'BAK').exists()
        for path in (folder/'Test Regular.ttf',folder/'BAK'/'Test Regular.ttf.original.bak'):
            actual=FileDates.capture(path)
            assert actual.modified_ns==expected.modified_ns,(path,actual,expected)
            assert actual.created_ns==expected.created_ns,(path,actual,expected)
        korean=Path(temporary)/'korean'
        korean.mkdir()
        source=korean/'source.ttf'
        make_font(source)
        native='\uc591\uc7ac\ube14\ub7ed\uccb4'
        raw=native.encode('euc_kr')
        from fontTools.ttLib.tables._n_a_m_e import NameRecord
        with TTFont(source) as font:
            font['name'].names=[]
            for language,payload in [(0x0412,b''.join(bytes((0,b)) for b in raw)),(0x0409,raw)]:
                record=NameRecord()
                record.nameID=4; record.platformID=3; record.platEncID=5; record.langID=language; record.string=payload
                font['name'].names.append(record)
            font.save(source)
        before=source.read_bytes()
        preview=subprocess.run([str(worker),str(korean),'--dry-run','--no-recursive'],capture_output=True,encoding='utf-8',check=True,timeout=60)
        assert 'YangJaeBeulLeogChe ['+native+'].ttf' in preview.stdout,preview.stdout
        assert source.read_bytes()==before
    print('Packaged GUI, logs beside the executable, recursion, normalization and original creation/modification dates: OK')


if __name__ == '__main__':
    main()
