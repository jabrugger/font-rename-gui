"""Read the CLI in a separate process; keep expensive work out of the UI."""
import os
import subprocess
import time
from PySide6.QtCore import QThread, Signal


class EngineRunner(QThread):
    output = Signal(str)
    completed = Signal(int)

    def __init__(self, command, cwd, parent=None):
        super().__init__(parent)
        self.command = command
        self.cwd = str(cwd)

    def run(self):
        code = 2
        try:
            env = dict(os.environ, PYTHONUTF8='1', PYTHONUNBUFFERED='1')
            kwargs = {}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            with subprocess.Popen(self.command, cwd=self.cwd, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                  text=True, encoding='utf-8', errors='replace', env=env,
                                  **kwargs) as child:
                batch = []
                previous = time.monotonic()
                for line in child.stdout:
                    batch.append(line.rstrip('\r\n'))
                    if len(batch) >= 100 or time.monotonic() - previous >= .08:
                        self.output.emit('\n'.join(batch))
                        batch.clear()
                        previous = time.monotonic()
                if batch:
                    self.output.emit('\n'.join(batch))
                code = child.wait()
        except Exception as exc:
            self.output.emit(f'ERROR (GUI): {type(exc).__name__}: {exc}')
        self.completed.emit(code)
