# SPDX-License-Identifier: BSD-2-Clause
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication


class Listener:
    def stopped(self, player):
        pass

    def ended(self, player):
        pass


class Player:
    """
    Player encapsulates playing a single file.
    """

    def __init__(self, path, listener):
        self._listener = listener
        self._path = path
        self._qmp = None

    @property
    def _player(self):
        if self._qmp is None:
            self._qmp = QMediaPlayer(QApplication.instance())
            self._qmp.setMedia(QMediaContent(QUrl("file:" + self._path)))
            self._qmp.mediaStatusChanged.connect(self._handleStatusChange)
        return self._qmp

    def _handleStatusChange(self, status):
        if status == self._player.EndOfMedia:
            self._listener.ended(self)

    def play(self):
        self._player.play()

    def pause(self):
        if self.is_playing():
            self._player.pause()

    def stop(self):
        self._player.stop()

    def is_playing(self):
        return self._player.state() == self._player.PlayingState
