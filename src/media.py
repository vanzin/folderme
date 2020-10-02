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

    def init_ui(self, ui):
        adapter = UIAdapter(ui, self)
        self.add_listener(adapter)

        self._player.durationChanged.connect(adapter.duration_changed)
        self._player.positionChanged.connect(adapter.position_changed)

    def set_position(self, position):
        self._player.setPosition(position)

    def position(self):
        return self._player.position()


class UIAdapter(Listener):
    def __init__(self, ui, player):
        self.ui = ui
        self.player = player
        self.duration = 0
        self.last_sec = 0
        self._slider_locked = False

        self.ui.tPosition.sliderPressed.connect(self.slider_pressed)
        self.ui.tPosition.sliderReleased.connect(self.slider_released)
        self.ui.tPosition.sliderMoved.connect(self.slider_moved)

    def _ms_to_text(self, ms):
        secs = int(ms / 1000)
        mins = int(secs / 60)
        secs -= mins * 60
        hrs = int(mins / 60)
        mins -= hrs * 60

        if hrs > 0:
            return f"{hrs}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def _normalize(self, duration):
        return duration - (duration % 1000)

    def _update_position(self, position):
        position = self._normalize(position)
        if self.duration:
            remaining = max(0, self.duration - position)
            self.ui.tRemaining.setText(self._ms_to_text(remaining))

        if self._slider_locked:
            return

        self.ui.tElapsed.setText(self._ms_to_text(position))
        self.ui.tPosition.setSliderPosition(position)

    def track_stopped(self, player):
        self._update_position(0)

    def track_ended(self, player):
        self.duration = 0

    def track_playing(self, player):
        self.ui.tPosition.setMinimum(0)
        self._update_position(0)

    def duration_changed(self, duration):
        duration = self._normalize(duration)
        self.ui.tRemaining.setText(self._ms_to_text(duration))
        self.ui.tPosition.setMinimum(0)
        self.ui.tPosition.setMaximum(duration)
        self.duration = duration

    def position_changed(self, position):
        if self._slider_locked:
            return

        sec = position // 1000
        if sec == self.last_sec:
            return
        self._update_position(self._normalize(position))

    def slider_pressed(self):
        self._slider_locked = True

    def slider_released(self):
        self._slider_locked = False
        self.player.set_position(self.ui.tPosition.sliderPosition())

        position = self._normalize(self.player.position())
        self.ui.tElapsed.setText(self._ms_to_text(position))

    def slider_moved(self):
        if not self._slider_locked:
            return

        position = self._normalize(self.ui.tPosition.sliderPosition())
        self.ui.tElapsed.setText(self._ms_to_text(position))
