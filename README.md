# Font Renamer GUI

A Windows desktop interface for the independent [font-rename-fm engine](https://github.com/jabrugger/font-rename-fm). The CLI remains available without Qt on Windows, Linux and macOS. This repository contains the optional desktop interface, not a second implementation of font renaming.

## Windows download

Download `FontRenamerGUI-0.2.0-windows-x64.zip` from [Releases](https://github.com/jabrugger/font-rename-gui/releases), extract the entire archive and open `FontRenamer/FontRenamer.exe`. Keep its folders together, including `worker` and `_internal`. Python is bundled; no Python installation is required. Windows x64 is the packaged target. The application is not code-signed.

1. Select one folder. Selecting another replaces it. **Include subfolders / Incluir subcarpetas** is checked by default; BAK folders are excluded.
2. Select internal-name cleanup, exact duplicate removal, transliteration and logging. Transliteration applies to names in other writing systems and retains the original name in brackets; it is not translation.
3. Run **Preview / Vista previa** and review the proposed operations. Fonts are not changed; a log is written if enabled.
4. Select **Apply changes / Aplicar cambios**. A confirmation always asks whether to run the process, with **No** as the default. It does not assume that changes will be necessary.

**Apply without preview / Aplicar sin vista previa** allows direct processing when selected. It is unchecked on every startup. Otherwise, changing the folder or processing options requires a fresh preview before applying.

The screen keeps the latest 3,000 lines to bound memory; an enabled log keeps the full output with the PC's local timestamp on each line. With no custom path, each processed font folder receives `BAK/font_renamer[YYYY-MM-DD].log`. Existing logs are appended. A custom path receives one combined log. **Clear screen / Limpiar pantalla** clears only the activity display and its placeholder, including while processing; it never truncates log files. **Open log / Abrir log** opens the most recently reported log.

The application includes its own executable and window icon. Font edits and their backups preserve original modification timestamps and Windows creation timestamps. Extracted collection members inherit the original collection timestamps; internal head timestamps are retained. Previously lost timestamps are not recovered automatically.

Cancellation requests a stop between fonts; it does not kill a process in the middle of a write. Completed changes remain. Internal edits have originals in sibling BAK folders. Ordinary renames and exact duplicate removal have no general undo. Start on a copy of your collection.

Spanish and English are available. Folder and option preferences are stored locally. No fonts, logs or telemetry are uploaded. Diagnostic output comes from the CLI and retains its English wording.

## Development

Python 3.12 or newer; the build used for Windows is Python 3.14. The GUI depends on the engine's `v0.3.1` Git tag, rather than the unrelated upstream PyPI release. Git is required for a source installation.

```console
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[build]"
.venv\Scripts\python launch_gui.py
.venv\Scripts\python -m unittest discover -v
.venv\Scripts\python tools/build_windows.py
```

Tests use generated fonts and Qt's offscreen platform. They cover preview immutability, real-engine application and deduplication, log creation, option mapping, safe cancellation requests, single-folder selection, recursion, per-folder logs, optional preview, confirmation defaults, screen clearing, locale changes and bounded log output. The Windows workflow builds the portable ZIP only after tests pass.

The GUI runs the CLI in an independent process. Its worker is a separate console-capable executable with output piped into the GUI, without a console window. This isolates the font processing from Qt and keeps the UI responsive. The CLI's hidden cancellation marker is an internal integration detail.

## License

GUI code: MIT. The engine retains its original MIT authorship. Qt for Python / PySide6 is distributed under its upstream licenses; dynamic libraries and third-party notices remain in the portable directory. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the included `licenses` folder.

## Changes and planned work

See [CHANGELOG.md](CHANGELOG.md). Comparing and consolidating different font versions is still a proposal, not a feature in this release. The GUI removes only byte-identical duplicates when that option is enabled.

## Versioning

See [VERSIONING.md](VERSIONING.md): corrections increment PATCH, new features increment MINOR, and major changes or a final release increment MAJOR.
