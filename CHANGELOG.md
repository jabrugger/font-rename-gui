# Changelog

## 0.4.0 - 2026-10-07

- Rename the application, distribution, module, commands, executables, settings and logs to Font Rename Neo GUI. Pin only font-rename-neo 0.4.0.
- Update documentation, download names and third-party notices.

## 0.3.0 - 2026-10-07

- Keep table selection and detail contents synchronized after filtering and refreshes; label the selected file explicitly.
- Enlarge the details area and show a draggable splitter. Make editable checkboxes visually distinct with boxed checkmarks and hover feedback.

- Bundle engine 0.3.2, fixing selection of valid Korean names over malformed guessed records; verify the packaged worker with a generated regression font.

- Compact single-line folder selection and options; a shared central area automatically switches from analysis activity to the preview list.
- Keep the list visible while applying; mark completed operations using confirmed worker results, errors in red, and unfinished operations as not processed.
- Add Play icons to Preview and Apply; the active action becomes Stop with a stop icon and cooperative cancellation tooltip. Remove the separate stop button.

- Bundle Spanish Qt translations so standard dialog buttons and controls follow the selected language; refresh option tooltips when switching languages.

- Link GUI and engine version information in the footer to their respective GitHub repositories.

- Fix corrupted accented UI text and remove the obsolete preview-first badge.

- Store GUI logs in one dated file under logs beside the executable, independent of the working directory.
- Configure and remember a custom log folder with a folder chooser. Create missing directories before processing; keep existing log files unchanged.
- Stop creating logs inside font-folder BAK directories.


## 0.2.0

- Select one folder with Include subfolders enabled by default.
- Allow applying without preview through an option disabled on every startup; always ask for confirmation with No as the default.
- Write automatic logs inside BAK in every processed font folder, or one combined log at a custom path.
- Fix Clear screen to clear activity and its placeholder without altering saved logs, including during processing.
- Explain that transliteration is for other writing systems and retains the original name.
- Add executable and window icons.
- Bundle font-rename-fm 0.3.1, preserving original modification and Windows creation timestamps on edits and backups.
- Sanitize the packaging environment to avoid unrelated DLLs; test the packaged worker, GUI preview, recursion, logging and timestamp preservation with generated fonts.
- Update usage and development documentation. No font-version consolidation is implemented.

## 0.1.0

- Initial Windows GUI with Spanish/English, preview, processing options, cancellation and bounded activity output.
- Portable package includes Python and the independent font-rename-fm engine.
