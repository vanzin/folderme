# SPDX-License-Identifier: BSD-2-Clause
import jsonpickle
import os
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSettings

SETTINGS = QSettings("vanzin.org", "folderme")


class ConfigObj:
    """
    Base class for config objects that disables serialization of "private" fields.
    """

    @classmethod
    def config_file_name(cls):
        return "{}.{}".format(cls.__module__, cls.__name__)

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def __setstate__(self, data):
        self.__init__()
        for k, v in data.items():
            setattr(self, k, v)


class EventSource:
    """
    Base class for objects that generate events. Handles listener registration and event
    firing.
    """

    def __init__(self):
        self._listeners = []

    def add_listener(self, l):
        self._listeners.append(l)

    def fire_event(self, handler, *args):
        for l in self._listeners:
            m = getattr(l, handler.__name__, None)
            if m:
                m(*args)


def init_ui(widget, src):
    path = os.path.join(os.path.dirname(__file__), "ui", src)
    uic.loadUi(path, widget)


def restore_ui(widget, name):
    data = SETTINGS.value(f"{name}/geometry")
    if data:
        widget.restoreGeometry(data)

    data = SETTINGS.value(f"{name}/windowState")
    if data:
        widget.restoreState(data)


def save_ui(widget, name):
    SETTINGS.setValue(f"{name}/geometry", widget.saveGeometry())
    if hasattr(widget, "saveState"):
        SETTINGS.setValue(f"{name}/windowState", widget.saveState())


def config_dir(create=False):
    path = os.path.dirname(SETTINGS.fileName())
    path = os.environ.get("FOLDERME_CONFIG", path)
    if create and not os.path.isdir(path):
        os.mkdir(path)
    return path


def _init_pickler():
    jsonpickle.set_preferred_backend("json")
    jsonpickle.set_encoder_options("json", indent=2)


def save_config(obj):
    _init_pickler()
    path = os.path.join(config_dir(create=True), obj.config_file_name())
    data = jsonpickle.encode(obj)
    with open(path, "wt", encoding="utf-8") as out:
        out.write(data)


def load_config(cls):
    path = os.path.join(config_dir(), cls.config_file_name())
    if os.path.isfile(path):
        return jsonpickle.decode(open(path).read())
    return cls()


def icon(name):
    return os.path.join(os.path.dirname(__file__), "icons", name)


def ms_to_text(ms):
    secs = int(ms / 1000)
    mins = int(secs / 60)
    secs -= mins * 60
    hrs = int(mins / 60)
    mins -= hrs * 60

    if hrs > 0:
        return f"{hrs}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def set_pixmap(label, pixmap):
    h = label.height()
    w = label.width()
    scaled = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    label.setPixmap(scaled)
