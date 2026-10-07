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
    log_directory: str = ''
    recursive: bool = True

    def resolved_log(self, folders):
        if not self.save_log:
            return None
        directory = Path(self.log_directory.strip()).expanduser().absolute() if self.log_directory.strip() else default_log_directory()
        if directory.exists() and not directory.is_dir():
            raise ValueError(f'Log location is not a folder: {directory}')
        return directory / f'font_rename_neo[{datetime.now().date().isoformat()}].log'


def default_log_directory():
    base = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
    return base / 'logs'


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
    if not options.recursive:
        args.append('--no-recursive')
    if options.normalize_internal:
        args.append('--normalize-internal')
    if not options.remove_duplicates:
        args.append('--keep-duplicates')
    if not options.transliterate:
        args.append('--no-transliterate')
    log = options.resolved_log(folders)
    if log is not None:
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(f'Cannot create log folder: {log.parent}: {exc}') from exc
        if log.is_dir():
            raise ValueError(f'Log destination is a folder: {log}')
        if log.suffix.casefold() in {'.ttf', '.otf', '.ttc', '.otc'} or log.name.casefold().endswith('.original.bak'):
            raise ValueError('The log must not overwrite a font or backup')
        args.extend(['--log', str(log)])
    if cancel_file is not None:
        args.extend(['--cancel-file', str(cancel_file)])
    return args, log


def worker_command():
    if getattr(sys, 'frozen', False):
        worker = Path(sys.executable).parent / 'worker' / 'FontRenameNeoWorker.exe'
        if not worker.is_file():
            raise FileNotFoundError(f'Bundled engine not found: {worker}')
        return [str(worker)]
    # pythonw has no console streams. The subprocess needs the console interpreter.
    interpreter = Path(sys.executable)
    if interpreter.name.casefold() == 'pythonw.exe':
        interpreter = interpreter.with_name('python.exe')
    return [str(interpreter), '-u', '-m', 'font_rename_neo_gui.worker']
