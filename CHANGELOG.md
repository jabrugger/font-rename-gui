# Changelog

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
