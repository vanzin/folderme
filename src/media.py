# SPDX-License-Identifier: BSD-2-Clause
import sys
import util

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication


class Listener:
    def track_paused(self, player):
        pass

    def track_playing(self, player):
        pass

    def track_stopped(self, player):
        pass

    def track_ended(self, player):
        pass


class Player(util.EventSource):
    """
    Player encapsulates playing a single file.
    """

    def __init__(self):
        util.EventSource.__init__(self)
        self._player = QMediaPlayer(QApplication.instance())
        self._player.mediaStatusChanged.connect(self._handleStatusChange)
        self._player.stateChanged.connect(self._handleStateChange)

    def _handleStatusChange(self, status):
        if status == self._player.EndOfMedia:
            self.fire_event(Listener.track_ended, self)

    def _handleStateChange(self, state):
        if state == self._player.StoppedState:
            self.fire_event(Listener.track_stopped, self)
        elif state == self._player.PlayingState:
            self.fire_event(Listener.track_playing, self)
        elif state == self._player.PausedState:
            self.fire_event(Listener.track_paused, self)

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

    def is_paused(self):
        return self._player.state() == self._player.PausedState
