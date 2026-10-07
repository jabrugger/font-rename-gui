# The worker remains a console executable so stdout/stderr can be piped reliably.
from font_rename_neo_gui.worker import main

if __name__ == '__main__':
    raise SystemExit(main())
