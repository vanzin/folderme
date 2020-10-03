# SPDX-License-Identifier: BSD-2-Clause
import os
import socket
import threading
import traceback
import sys
import util
from PyQt5.QtWidgets import QApplication

SOCKET_PATH = "\0" + os.path.join(util.config_dir(), "cmd.socket")


class Server:
    def __init__(self, ui):
        self.ui = ui

    def serve(self):
        t = threading.Thread(target=self._serve, daemon=True)
        t.start()

    def _serve(self):
        s = socket.socket(socket.AF_UNIX)
        try:
            s.bind(SOCKET_PATH)
            s.listen(1)
        except:
            traceback.print_exc()
            QApplication.instance().exit(1)
            return

        while True:
            try:
                c, _ = s.accept()
                with c:
                    cmd = c.recv(1024).decode("utf-8").split("\n")[0]
                    self._do_command(cmd)
            except:
                print("Error in socket receive:", file=sys.stderr)
                traceback.print_exc()

        s.close()

    def _do_command(self, cmd):
        if cmd == "quit":
            self.ui.handleQuit()
        else:
            print(f"Unrecognized command: {cmd}")


def send(cmd):
    s = socket.socket(socket.AF_UNIX)
    with s:
        s.connect(SOCKET_PATH)
        s.send(cmd.encode("utf-8"))
