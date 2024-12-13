# SPDX-License-Identifier: BSD-2-Clause
import os
import time
import traceback
from contextlib import contextmanager

import jsonpickle
from PySide6.QtCore import QSettings
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QPixmapCache
from PySide6.QtUiTools import loadUiType

SETTINGS = QSettings("vanzin.org", "folderme")


class ConfigObj:
    """
    Base class for config objects that disables serialization of "private" fields.
    """

    SAVE_ENABLED = True

    @classmethod
    def load(cls):
        path = os.path.join(config_dir(), cls.config_file_name())
        if os.path.isfile(path):
            return jsonpickle.decode(open(path).read())
        return cls()

    @classmethod
    def config_file_name(cls):
        return "{}.{}".format(cls.__module__, cls.__name__)

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def __setstate__(self, data):
        self.__init__()
        for k, v in data.items():
            setattr(self, k, v)

    def save(self):
        if self.SAVE_ENABLED:
            jsonpickle.set_preferred_backend("json")
            jsonpickle.set_encoder_options("json", indent=2)
            path = os.path.join(config_dir(create=True), self.config_file_name())
            data = jsonpickle.encode(self)
            with open(path, "wt", encoding="utf-8") as out:
                out.write(data)


class EventBus:
    """
    An event bus for `Listener` events.
    """

    FIRING = False
    QUEUE = []
    LISTENERS = []

    @classmethod
    def add(cls, l):
        cls.LISTENERS.append(l)

    @classmethod
    def send(cls, handler, *args):
        if cls.FIRING:
            QTimer.singleShot(0, lambda: cls.send(handler, *args))
            return

        for l in cls.LISTENERS:
            m = getattr(l, handler.__name__, None)
            if m:
                try:
                    m(*args)
                except:
                    traceback.print_exc()

        cls.FIRING = False


class Listener:
    def collection_changed(self):
        pass

    def playlist_changed(self):
        pass

    def playlist_ended(self):
        pass

    def track_paused(self, track):
        pass

    def track_playing(self, track):
        pass

    def track_position_changed(self, track, position):
        pass

    def track_stopped(self, track):
        pass

    def track_ended(self, track):
        pass

    def track_changed(self, track):
        pass

    def ui_resized(self, widget):
        pass

    def ui_exit(self):
        pass


class PixmapCache:
    def __init__(self):
        self._cache = QPixmapCache()
        self._cache.setCacheLimit(64 * 1024 * 1024)

    def get_cover(self, album):
        track = album.tracks[0]
        pixmap = self._cache.find(os.path.dirname(track.info.path))
        if not pixmap:
            pixmap = QPixmap()
            cover = track.info.cover_art()
            if cover:
                pixmap.loadFromData(cover)
            else:
                pixmap.load(icon("blank.jpg"))
            self._cache.insert(track.info.path, pixmap)
        return pixmap

    def remove_cover(self, album):
        track = album.tracks[0]
        self._cache.remove(os.path.dirname(track.path))

    def get_icon(self, name):
        pixmap = self._cache.find(name)
        if not pixmap:
            pixmap = QPixmap()
            pixmap.load(icon(name))
            self._cache.insert(name, pixmap)
        return pixmap


class ElisionHelper:
    def __init__(self, widget, label, text, padding):
        self.widget = widget
        self.label = label
        self.text = text
        self.padding = padding

        self._widget_resized = widget.resizeEvent
        widget.resizeEvent = self._resized
        self._set_label_text()

    def _resized(self, e):
        self._widget_resized(e)
        self._set_label_text()

    def _set_label_text(self):
        fm = QFontMetrics(self.label.font())
        elided = fm.elidedText(
            self.text, Qt.ElideRight, self.widget.width() - self.padding
        )
        self.label.setText(elided)
        if elided != self.text:
            self.label.setToolTip(self.text)
        else:
            self.label.setToolTip(None)


def compile_ui(src):
    path = os.path.join(os.path.dirname(__file__), "ui", src)
    form, qtclass = loadUiType(path)

    class _WidgetBase(form, qtclass):
        def __init__(self, parent=None):
            qtclass.__init__(self, parent)
            form.__init__(self)
            self.setupUi(self)

    return _WidgetBase


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


def print_error():
    import traceback

    traceback.print_exc()


@contextmanager
def profile(name):
    t1 = int(time.time() * 1000)
    yield
    t2 = int(time.time() * 1000)
    print(f"{name} took {t2 - t1} ms")
