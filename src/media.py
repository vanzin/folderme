# SPDX-License-Identifier: BSD-2-Clause
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication


class Listener:
    def paused(self, player):
        pass

    def playing(self, player):
        pass

    def stopped(self, player):
        pass

    def track_ended(self, player):
        pass


class Player:
    """
    Player encapsulates playing a single file.
    """

    def __init__(self, listener):
        self._listener = listener
        self._player = QMediaPlayer(QApplication.instance())
        self._player.mediaStatusChanged.connect(self._handleStatusChange)
        self._player.stateChanged.connect(self._handleStateChange)

    def _handleStatusChange(self, status):
        if status == self._player.EndOfMedia:
            print("Track ended")
            self._listener.ended(self)

    def _handleStateChange(self, state):
        if state == self._player.StoppedState:
            self._listener.stopped(self)
        elif state == self._player.PlayingState:
            self._listener.playing(self)
        elif state == self._player.PausedState:
            self._listener.paused(self)

    def play(self, track=None):
        if track:
            if self.is_playing():
                self.stop()
            print(f"Playing track {track.path}")
            self._player.setMedia(QMediaContent(QUrl("file:" + track.path)))
        self._player.play()

    def pause(self):
        if self.is_playing():
            self._player.pause()

    def stop(self):
        self._player.stop()

    def is_playing(self):
        return self._player.state() == self._player.PlayingState
