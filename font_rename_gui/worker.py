"""GUI integration with the pinned engine; deduplication spans the whole run."""
import contextlib
import sys
from datetime import datetime
from pathlib import Path
from font_rename_fm import rename as engine


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    recursive = '--no-recursive' not in arguments
    per_folder = '--log-per-folder' in arguments
    arguments = [a for a in arguments if a not in ('--no-recursive', '--log-per-folder')]
    original_collect, original_run = engine.collect_files, engine.run_command

    def collect(paths):
        if recursive:
            return original_collect(paths)
        candidates = []
        for path in paths:
            candidates.extend([p for p in path.iterdir() if p.is_file()] if path.is_dir() else [path])
        return original_collect(candidates)

    def run(args, parser):
        try:
            files = collect(args.files)
            folders = sorted({p.parent for p in files}, key=lambda p: str(p).casefold())
            if not folders:
                folders = [p.resolve() for p in args.files if p.is_dir()]
            logs = {p: p/'BAK'/f'font_renamer[{datetime.now().date().isoformat()}].log' for p in folders}
            # Validate all destinations before any font mutation.
            for log in logs.values():
                if log.parent.is_symlink() or log.is_symlink():
                    raise ValueError(f'Unsafe log destination: {log}')
                log.parent.mkdir(exist_ok=True)
                with log.open('a', encoding='utf-8'):
                    pass
        except (OSError, ValueError) as exc:
            parser.error(f'Cannot prepare logs; no fonts changed: {exc}')
        renamer = engine.Renamer(args.apply, args.keep_duplicates, not args.no_transliterate,
                                args.cancel_file.exists if args.cancel_file else None)

        @contextlib.contextmanager
        def logging(folder, phase):
            print(f'LOG: {logs[folder]}')
            with logs[folder].open('a', encoding='utf-8') as output, engine.text_log(output, arguments):
                print(f'PHASE: {phase}')
                print('APPLY' if args.apply else 'PREVIEW: no fonts will be changed.')
                yield

        for folder in folders:
            if renamer.should_cancel():
                break
            with logging(folder, 'RENAME'):
                renamer.process([p for p in files if p.parent == folder])
        # Normalize only after all original byte identities have been compared.
        if args.normalize_internal and not renamer.should_cancel():
            reserved = renamer.reserved
            try:
                for folder in folders:
                    if renamer.should_cancel():
                        break
                    renamer.reserved = {key: ref for key,ref in reserved.items() if ref.path.parent == folder}
                    with logging(folder, 'INTERNAL'):
                        normalized = engine.normalize_retained_names(renamer)
                        print(f'{normalized} fonts with internal name changes.')
            finally:
                renamer.reserved = reserved
        result = 130 if renamer.cancelled else (1 if renamer.errors else 0)
        summary = f'{renamer.changed} changes, {renamer.duplicates} byte-identical duplicates, {renamer.errors} errors.'
        print(summary)
        for folder in folders:
            with logging(folder, 'SUMMARY'):
                print('Whole-run totals: ' + summary)
                if renamer.cancelled:
                    print('CANCELLED: stopped between fonts; completed changes remain.')
                print(f'EXIT STATUS: {result}')
        return result

    engine.collect_files = collect
    if per_folder:
        engine.run_command = run
    try:
        return engine.main(arguments)
    finally:
        engine.collect_files, engine.run_command = original_collect, original_run


if __name__ == '__main__':
    raise SystemExit(main())
