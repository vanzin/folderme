# SPDX-License-Identifier: BSD-2-Clause
import app
import util
from PySide6.QtCore import QPoint
from PySide6.QtCore import QSize
from PySide6.QtCore import QTimer
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtGui import QPixmap


def init():
    OSD.instance(Message)
    OSD.instance(Track)


def show_msg(msg):
    OSD.instance(Message).show_osd(msg)


def show_track(track):
    OSD.instance(Track).show_osd(track)


class OSD:
    _INSTANCES = {}

    _TIMER = None
    _WINDOW = None

    @classmethod
    def instance(cls, impl):
        if impl not in cls._INSTANCES:
            cls._INSTANCES[impl] = impl()
        return cls._INSTANCES[impl]

    @staticmethod
    def init_osd():
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_X11DoNotAcceptFocus)
        self.setWindowOpacity(0.80)

    @staticmethod
    def _pre_show():
        if OSD._TIMER:
            OSD._TIMER.stop()
            OSD._TIMER = None

        if OSD._WINDOW:
            OSD._WINDOW.close()

    @staticmethod
    def _show_osd(wnd):
        psize = wnd.sizeHint()

        sw = QGuiApplication.primaryScreen().availableSize().width()
        w = psize.width()
        if psize.width() > sw:
            w = sw / 2

        wnd.setFocusPolicy(Qt.NoFocus)
        wnd.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.WindowTransparentForInput
            | Qt.Window
        )
        wnd.setAttribute(Qt.WA_ShowWithoutActivating)
        wnd.setAttribute(Qt.WA_X11DoNotAcceptFocus)
        wnd.setWindowOpacity(0.80)

        wnd.resize(QSize(w, psize.height()))

        y = 64
        x = sw // 2 - w // 2
        wnd.move(QPoint(x, y))

        show_timer = QTimer()
        show_timer.setSingleShot(True)
        show_timer.timeout.connect(lambda: OSD._close(wnd))
        show_timer.start(2000)

        OSD._TIMER = show_timer
        OSD._WINDOW = wnd
        QTimer.singleShot(0, wnd.show)

    @staticmethod
    def _close(wnd):
        OSD._TIMER = None
        OSD._WINDOW = None
        wnd.close()


class Message(util.compile_ui("osd_msg.ui")):
    def __init__(self):
        super().__init__()

    def show_osd(self, msg):
        OSD._pre_show()
        self.lMessage.setText(msg)
        OSD._show_osd(self)


class Track(util.compile_ui("osd.ui")):
    def __init__(self):
        super().__init__()
        util.EventBus.add(self)

    def track_playing(self, track):
        self.show_osd(track)

    def track_paused(self, track):
        self.show_osd(track)

    def track_stopped(self, track):
        self.show_osd(track)

    def track_changed(self, track):
        if not app.get().playlist.is_playing():
            self.show_osd(track)

    def show_osd(self, track):
        OSD._pre_show()

        if not track:
            track = app.get().playlist.current_track()
            if track:
                track = track.info

        status = "Stopped"
        if app.get().playlist.is_playing():
            status = "Playing"
        elif app.get().playlist.is_paused():
            status = "Paused"

        if not track:
            pixmap = QPixmap()
            pixmap.load(util.icon("blank.jpg"))
            util.set_pixmap(self.cover, pixmap)
            self.artist.setText("")
            self.album.setText("")
            self.track.setText("")
        else:
            cover = track.cover_art()
            pixmap = QPixmap()
            if cover:
                pixmap.loadFromData(cover)
            else:
                pixmap.load(util.icon("blank.jpg"))

            util.set_pixmap(self.cover, pixmap)
            self.artist.setText(track.artist)
            self.album.setText(track.album)
            self.track.setText(track.title)

        self.status.setText(status)
        OSD._show_osd(self)


if __name__ == "__main__":
    import collection
    import sys
    import time

    class Args(object):
        pass

    args = Args()
    args.no_save = True
    args.no_lastfm = True
    app.init(args)
    init()

    def msg_test():
        show_msg("Hello this is a message!")

    def track_test():
        t = collection.Track()
        t.artist = "Artist"
        t.album = "Album"
        t.title = "Title"
        show_track(t)

    QTimer.singleShot(1000, msg_test)
    QTimer.singleShot(3000, track_test)
    QTimer.singleShot(5000, lambda: app.get().exit())
    sys.exit(app.get().exec_())
