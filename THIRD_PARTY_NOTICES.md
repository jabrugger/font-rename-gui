# Third-party components

The GUI code is MIT-licensed. The Windows portable distribution also includes:

- **font-rename-fm**: MIT; original authors Jay Soren / Futuremotion and upstream contributors, fork maintained by jabrugger. Source: https://github.com/jabrugger/font-rename-fm/tree/v0.3.0
- **PySide6, Qt and Shiboken**: upstream LGPL/GPL/commercial licensing as specified in their accompanying notices. This distribution uses the applicable open-source LGPL terms and keeps Qt shared libraries dynamically linked and replaceable. Source and licensing: https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://www.qt.io/licensing/open-source-lgpl-obligations
- **fontTools**: upstream MIT license. Source: https://github.com/fonttools/fonttools
- **AnyAscii**: upstream ISC license. Source: https://github.com/anyascii/anyascii
- **faust-cchardet**: upstream notices, including the Mozilla charset detector components. Source: https://github.com/faust-streaming/cChardet
- **CPython**: Python Software Foundation license. Source: https://www.python.org/downloads/source/
- **PyInstaller bootloader**: GPL with the bootloader distribution exception. Source: https://github.com/pyinstaller/pyinstaller

The build copies the installed packages' license texts and versions to `licenses/`. This repository's MIT license does not replace those licenses. Users may replace compatible dynamic libraries; the package is not designed to prevent modification or debugging of LGPL components. No font files are bundled.
