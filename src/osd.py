# SPDX-License-Identifier: BSD-2-Clause
import app
import util
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtGui import QPixmap


def init():
    Message.instance()
    Track.instance()


def show_msg(msg):
    Message.instance().show_osd(msg)


def show_track(track):
    Track.instance().show_osd(track)


class BaseOSD:
    _INSTANCE = None

    _TIMER = None
    _WINDOW = None

    @classmethod
    def instance(cls):
        if not cls._INSTANCE:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def __init__(self):
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.WindowTransparentForInput
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowOpacity(0.80)

    def _pre_show(self):
        if BaseOSD._TIMER:
            BaseOSD._TIMER.stop()
            BaseOSD._TIMER = None

        if BaseOSD._WINDOW:
            BaseOSD._WINDOW.close()

    def _show_osd(self):
        psize = self.sizeHint()

        sw = QGuiApplication.primaryScreen().availableSize().width()
        w = psize.width()
        if psize.width() > sw:
            w = sw / 2

        self.resize(QSize(w, psize.height()))

        y = 64
        x = sw // 2 - w // 2
        self.move(QPoint(x, y))

        show_timer = QTimer()
        show_timer.setSingleShot(True)
        show_timer.timeout.connect(self._close)
        show_timer.start(2000)

        BaseOSD._TIMER = show_timer
        BaseOSD._WINDOW = self
        QTimer.singleShot(0, self.show)

    def _close(self):
        BaseOSD._TIMER = None
        BaseOSD._WINDOW = None
        self.close()


class Message(util.compile_ui("osd_msg.ui"), BaseOSD):
    def __init__(self):
        super().__init__()
        BaseOSD.__init__(self)

    def show_osd(self, msg):
        self._pre_show()
        self.lMessage.setText(msg)
        self._show_osd()


class Track(util.compile_ui("osd.ui"), BaseOSD):
    def __init__(self):
        super().__init__()
        BaseOSD.__init__(self)
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
        self._pre_show()

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
        self._show_osd()


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
