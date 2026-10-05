# Font Renamer GUI

A Windows desktop interface for the independent [font-rename-fm engine](https://github.com/jabrugger/font-rename-fm). The CLI remains available without Qt on Windows, Linux and macOS. This repository contains the optional desktop interface, not a second implementation of font renaming.

## Windows download

Download `FontRenamerGUI-0.1.0-windows-x64.zip` from [Releases](https://github.com/jabrugger/font-rename-gui/releases), extract the entire archive and open `FontRenamer/FontRenamer.exe`. Keep its folders together, including `worker` and `_internal`. Python is bundled; no Python installation is required. Windows x64 is the packaged target. The application is not code-signed.

1. Add one or more folders. Subfolders are included; BAK folders are excluded. Overlapping selections are consolidated.
2. Select internal-name cleanup, exact duplicate removal, transliteration and logging.
3. Run **Preview / Vista previa**. Fonts are not changed; a log is written if enabled.
4. Review the output and select **Apply changes / Aplicar cambios**. Applying asks for confirmation. Changing folders or options requires a new preview.

The screen keeps the latest 3,000 lines to bound memory; an enabled log keeps the full output with the PC's local timestamp on each line. With no custom log path, the log is placed in the first selected folder as `font_renamer[YYYY-MM-DD].log`. Existing logs are appended. A folder chooser adds one directory at a time; repeat it to select several folders.

Cancellation requests a stop between fonts; it does not kill a process in the middle of a write. Completed changes remain. Internal edits have originals in sibling BAK folders. Ordinary renames and exact duplicate removal have no general undo. Start on a copy of your collection.

Spanish and English are available. Folder and option preferences are stored locally. No fonts, logs or telemetry are uploaded. Diagnostic output comes from the CLI and retains its English wording.

## Development

Python 3.12 or newer; the build used for Windows is Python 3.14. The GUI depends on the engine's `v0.3.0` Git tag, rather than the unrelated upstream PyPI release. Git is required for a source installation.

```console
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[build]"
.venv\Scripts\python launch_gui.py
.venv\Scripts\python -m unittest discover -v
.venv\Scripts\python tools/build_windows.py
```

Tests use generated fonts and Qt's offscreen platform. They cover preview immutability, real-engine application and deduplication, log creation, option mapping, safe cancellation requests, overlap selection, locale changes and bounded log output. The Windows workflow builds the portable ZIP only after tests pass.

The GUI runs the CLI in an independent process. Its worker is a separate console-capable executable with output piped into the GUI, without a console window. This isolates the font processing from Qt and keeps the UI responsive. The CLI's hidden cancellation marker is an internal integration detail.

## License

GUI code: MIT. The engine retains its original MIT authorship. Qt for Python / PySide6 is distributed under its upstream licenses; dynamic libraries and third-party notices remain in the portable directory. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the included `licenses` folder.
