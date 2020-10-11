# SPDX-License-Identifier: BSD-2-Clause
import util
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QGuiApplication, QPixmap
from PyQt5.QtWidgets import QMainWindow


class OSD(QMainWindow):
    def __init__(self, playlist):
        QMainWindow.__init__(self)
        util.init_ui(self, "osd.ui")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.80)
        self.timer = None
        self.playlist = playlist
        self.playlist.player().add_listener(self)

    def track_playing(self, track):
        self.show_osd(track)

    def track_paused(self, track):
        self.show_osd(track)

    def track_stopped(self, track):
        self.show_osd(track)

    def show_osd(self, track):
        if self.timer:
            self.timer.stop()

        if self.isVisible():
            self.close()

        if not track:
            track = self.playlist.current_track()
            if track:
                track = track.info

        status = "Stopped"
        if self.playlist.player().is_playing():
            status = "Playing"
        elif self.playlist.player().is_paused():
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

        y = 64
        w = self.width()
        sw = QGuiApplication.primaryScreen().availableSize().width()
        x = sw // 2 - w // 2
        self.move(QPoint(x, y))

        self.status.setText(status)
        self.timer = QTimer.singleShot(2000, self.close)
        self.show()
