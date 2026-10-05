"""CLI integration without a dependency on the GUI framework."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys


@dataclass(frozen=True)
class Options:
    normalize_internal: bool = True
    remove_duplicates: bool = True
    transliterate: bool = True
    save_log: bool = True
    log_path: str = ''

    def resolved_log(self, folders):
        if not self.save_log:
            return None
        if self.log_path.strip():
            return Path(self.log_path.strip()).absolute()
        return Path(folders[0]) / f'font_renamer[{datetime.now().date().isoformat()}].log'


def unique_folders(folders):
    result = []
    for value in folders:
        path = Path(value).resolve()
        if not path.is_dir():
            raise ValueError(f'Folder does not exist: {value}')
        if path.name.casefold() == 'bak':
            raise ValueError(f'Backup folders are excluded: {value}')
        if path not in result:
            result.append(path)
    # Avoid scanning the same tree through overlapping selections.
    return [p for p in result if not any(other != p and other in p.parents for other in result)]


def build_arguments(folders, options, apply=False, cancel_file=None):
    folders = unique_folders(folders)
    if not folders:
        raise ValueError('Select at least one folder')
    args = [str(p) for p in folders]
    args.append('--apply' if apply else '--dry-run')
    if options.normalize_internal:
        args.append('--normalize-internal')
    if not options.remove_duplicates:
        args.append('--keep-duplicates')
    if not options.transliterate:
        args.append('--no-transliterate')
    log = options.resolved_log(folders)
    if log is not None:
        if not log.parent.is_dir() or log.is_dir():
            raise ValueError(f'Log folder does not exist: {log.parent}')
        if log.suffix.casefold() in {'.ttf', '.otf', '.ttc', '.otc'} or log.name.casefold().endswith('.original.bak'):
            raise ValueError('The log must not overwrite a font or backup')
        args.extend(['--log', str(log)])
    if cancel_file is not None:
        args.extend(['--cancel-file', str(cancel_file)])
    return args, log


def worker_command():
    if getattr(sys, 'frozen', False):
        worker = Path(sys.executable).parent / 'worker' / 'FontRenamerWorker.exe'
        if not worker.is_file():
            raise FileNotFoundError(f'Bundled engine not found: {worker}')
        return [str(worker)]
    # pythonw has no console streams. The subprocess needs the console interpreter.
    interpreter = Path(sys.executable)
    if interpreter.name.casefold() == 'pythonw.exe':
        interpreter = interpreter.with_name('python.exe')
    return [str(interpreter), '-u', '-m', 'font_rename_fm.rename']
