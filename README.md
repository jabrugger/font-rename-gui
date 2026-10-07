# Font Rename Neo GUI

A Windows desktop interface for the independent [Font Rename Neo engine](https://github.com/jabrugger/font-rename-neo). The CLI remains available without Qt on Windows, Linux and macOS. This repository contains the optional desktop interface, not a second implementation of font renaming.

The GUI uses only the `font-rename-neo` distribution and `font_rename_neo` module. Its bundled worker cannot select an installed `font-rename-fm`. Settings and logs have separate Neo names; earlier settings and logs remain untouched. The footer identifies both bundled versions.

## Windows download

Download `FontRenameNeoGUI-0.4.0-windows-x64.zip` from [Releases](https://github.com/jabrugger/font-rename-neo-gui/releases), extract the entire archive and open `FontRenameNeo/FontRenameNeo.exe`. Keep its folders together, including `worker` and `_internal`. Python is bundled; no Python installation is required. Windows x64 is the packaged target. The application is not code-signed.

1. Select one folder. Selecting another replaces it. **Include subfolders / Incluir subcarpetas** is checked by default; BAK folders are excluded.
2. Select internal-name cleanup, exact duplicate removal, transliteration and logging. Transliteration applies to names in other writing systems and retains the original name in brackets; it is not translation.
3. Run **Preview / Vista previa** and review the proposed operations. Fonts are not changed; a log is written if enabled.
4. Select **Apply changes / Aplicar cambios**. A confirmation always asks whether to run the process, with **No** as the default. It does not assume that changes will be necessary.

## Preview and processing results

Folder selection uses one line with compact options below it. The central area displays activity while analyzing, then automatically displays the searchable and filterable preview list and per-file details. During application the same list shows pending, processing, confirmed completion, unchanged, error and not-processed states. Green completion marks are emitted only after the corresponding engine operation returns successfully; internal edits have a separate result, so a successful rename cannot hide a failed normalization. The full log remains accessible through Open log. Filters affect presentation only, not which files are processed.

Preview and Apply have Play icons. While one is active it becomes Stop with a stop icon; the other is disabled. Stop requests cooperative cancellation between font operations. Completed changes remain; the list retains their results and marks unfinished operations as not processed. The Stop action is available only while processing.

The detail panel follows the selected file when sorting, filtering or refreshing. Drag the separator to resize the list and detail panel. Option checkboxes use visible boxes and hover feedback.

**Apply without preview / Aplicar sin vista previa** allows direct processing when selected. It is unchecked on every startup. Otherwise, changing the folder or processing options requires a fresh preview before applying.

The screen keeps the latest 3,000 lines to bound memory; an enabled log keeps the full output with the PC's local timestamp on each line. With no custom folder, output is appended to `logs/font_rename_neo[YYYY-MM-DD].log` beside `FontRenameNeo.exe`, independently of the working directory and font folders. The **Logs…** button lets you type or choose a different log folder; this preference is saved locally. Missing folders are created before processing; a creation/open failure stops processing before font changes. All processed folders share the same dated log. Clearing the configured folder restores the default. Source runs use `logs` in the project directory. Old per-folder logs stay where they are. **Clear screen / Limpiar pantalla** clears only the activity display and its placeholder, including while processing; it never truncates log files. **Open log / Abrir log** opens the most recently reported log.

The application includes its own executable and window icon. Font edits and their backups preserve original modification timestamps and Windows creation timestamps. Extracted collection members inherit the original collection timestamps; internal head timestamps are retained. Previously lost timestamps are not recovered automatically.

Cancellation requests a stop between fonts; it does not kill a process in the middle of a write. Completed changes remain. Internal edits have originals in sibling BAK folders. Ordinary renames and exact duplicate removal have no general undo. Start on a copy of your collection.

Spanish and English are available. Folder and option preferences are stored locally. No fonts, logs or telemetry are uploaded. Diagnostic output comes from the CLI and retains its English wording.

## Development

Python 3.12 or newer; the build used for Windows is Python 3.14. The GUI bundles Font Rename Neo 0.4.0 and depends on the engine's `v0.4.0` Git tag, rather than the unrelated upstream PyPI release. Git is required for a source installation.

```console
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[build]"
.venv\Scripts\python launch_gui.py
.venv\Scripts\python -m unittest discover -v
.venv\Scripts\python tools/build_windows.py
```

27 tests use generated fonts and Qt's offscreen platform. They cover preview immutability, real-engine application and deduplication, log creation, option mapping, safe cancellation requests, single-folder selection, recursion, centralized logs, optional preview, confirmation defaults, screen clearing, locale changes and bounded log output, table/detail synchronization, per-file confirmed results and collection-member status separation. The Windows workflow builds the portable ZIP only after tests pass.

The GUI runs the CLI in an independent process. Its worker is a separate console-capable executable with output piped into the GUI, without a console window. This isolates the font processing from Qt and keeps the UI responsive. The CLI's hidden cancellation marker is an internal integration detail.

## License

GUI code: MIT. The engine retains its original MIT authorship. Qt for Python / PySide6 is distributed under its upstream licenses; dynamic libraries and third-party notices remain in the portable directory. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the included `licenses` folder.

## Changes and planned work

See [CHANGELOG.md](CHANGELOG.md). Comparing and consolidating different font versions is still a proposal, not a feature in this release. The GUI removes only byte-identical duplicates when that option is enabled.

## Versioning

See [VERSIONING.md](VERSIONING.md): corrections increment PATCH, new features increment MINOR, and major changes or a final release increment MAJOR.
