# SPDX-License-Identifier: BSD-2-Clause
import util
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QGuiApplication, QPixmap
from PyQt5.QtWidgets import QMainWindow


class OSD(QMainWindow):
    INSTANCE = None

    def __init__(self, player):
        QMainWindow.__init__(self)
        util.init_ui(self, "osd.ui")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowOpacity(0.80)

        if OSD.INSTANCE:
            OSD.INSTANCE.close()
            OSD.INSTANCE = None

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
        QTimer.singleShot(2000, self._close)
        OSD.INSTANCE = self
        self.show()

    def _close(self):
        OSD.INSTANCE = None
        self.close()
