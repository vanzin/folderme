import os
from PyQt5 import uic


def init_ui(widget, src):
    path = os.path.join(os.path.dirname(__file__), "ui", src)
    uic.loadUi(path, widget)
