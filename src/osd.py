# SPDX-License-Identifier: BSD-2-Clause
import util
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QGuiApplication, QPixmap
from PyQt5.QtWidgets import QMainWindow


class OSD(QMainWindow):
    def __init__(self, player):
        QMainWindow.__init__(self)
        util.init_ui(self, "osd.ui")
        player.add_listener(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowOpacity(0.80)
        self.timer = None

    def track_playing(self, player):
        self._show(player)

    def track_paused(self, player):
        self._show(player)

    def track_stopped(self, player):
        self._show(player)

    def _show(self, player):
        if self.timer:
            self.timer.stop()

        if self.isVisible():
            self.close()

        status = "Stopped"
        if player.is_playing():
            status = "Playing"
        elif player.is_paused():
            status = "Paused"

        track = player.track()
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
