# SPDX-License-Identifier: BSD-2-Clause
import os

import util
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QAbstractSlider


class Player:
    """
    Player encapsulates playing a single file.
    """

    def __init__(self, parent):
        self._player = QMediaPlayer(parent)
        self._player.setAudioOutput(QAudioOutput(parent))
        self._player.mediaStatusChanged.connect(self._handleMediaChange)
        self._player.playbackStateChanged.connect(self._handlePlaybackChange)
        self._player.positionChanged.connect(self._handlePositionChange)
        self._track = None

    def _handleMediaChange(self, status):
        if status == QMediaPlayer.EndOfMedia:
            util.EventBus.send(util.Listener.track_ended, self._track)

    def _handlePlaybackChange(self, status):
        if status == QMediaPlayer.PlayingState:
            util.EventBus.send(util.Listener.track_playing, self._track)
        elif status == QMediaPlayer.StoppedState:
            util.EventBus.send(util.Listener.track_stopped, self._track)
        elif status == QMediaPlayer.PausedState:
            util.EventBus.send(util.Listener.track_paused, self._track)

    def _handlePositionChange(self, position):
        util.EventBus.send(util.Listener.track_position_changed, self._track, position)

    def play(self, track=None):
        if track:
            print(f"Playing track {track.path}")
            self.set_track(track)
        if self._track:
            self._player.play()

    def pause(self):
        if self.is_playing():
            self._player.pause()

    def stop(self):
        if self.is_playing() or self.is_paused():
            self._player.stop()

    def is_playing(self):
        return self._player.playbackState() == QMediaPlayer.PlayingState

    def is_paused(self):
        return self._player.playbackState() == QMediaPlayer.PausedState

    def init_ui(self, ui):
        adapter = UIAdapter(ui, self)
        util.EventBus.add(adapter)
        self._player.durationChanged.connect(adapter.duration_changed)

    def set_position(self, position):
        self._player.setPosition(position)

    def position(self):
        return self._player.position()

    def track(self):
        return self._track

    def set_track(self, track):
        if os.path.isfile(track.path):
            self._player.setSource(QUrl.fromLocalFile(track.path))
            self._track = track
            util.EventBus.send(util.Listener.track_changed, track)


class UIAdapter(util.Listener):
    def __init__(self, ui, player):
        self.ui = ui
        self.player = player
        self.duration = 0
        self.last_sec = 0
        self._slider_locked = False

        self.ui.tPosition.sliderPressed.connect(self.slider_pressed)
        self.ui.tPosition.sliderReleased.connect(self.slider_released)
        self.ui.tPosition.sliderMoved.connect(self.slider_moved)
        self.ui.tPosition.actionTriggered.connect(self.action_triggered)

    def _normalize(self, duration):
        return duration - (duration % 1000)

    def _update_position(self, position):
        position = self._normalize(position)
        if self.duration:
            remaining = max(0, self.duration - position)
            self.ui.tRemaining.setText(util.ms_to_text(remaining))

        if self._slider_locked:
            return

        self.ui.tElapsed.setText(util.ms_to_text(position))
        self.ui.tPosition.setSliderPosition(position)

    def track_stopped(self, track):
        self._update_position(0)

    def track_ended(self, track):
        self.duration = 0

    def track_playing(self, track):
        self.ui.tPosition.setMinimum(0)
        self._update_position(0)

    def track_changed(self, track):
        self.duration_changed(track.duration_ms)
        self._update_position(0)

    def duration_changed(self, duration):
        duration = self._normalize(duration)
        self.ui.tRemaining.setText(util.ms_to_text(duration))
        self.ui.tPosition.setMinimum(0)
        self.ui.tPosition.setMaximum(duration)
        self.duration = duration

    def track_position_changed(self, track, position):
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
        self.ui.tElapsed.setText(util.ms_to_text(position))

    def slider_moved(self):
        if not self._slider_locked:
            return

        position = self._normalize(self.ui.tPosition.sliderPosition())
        self.ui.tElapsed.setText(util.ms_to_text(position))

    def action_triggered(self, action):
        if self._slider_locked:
            return

        if action == QAbstractSlider.SliderSingleStepAdd:
            step = self.duration // 100
        elif action == QAbstractSlider.SliderSingleStepSub:
            step = -self.duration // 100
        elif action == QAbstractSlider.SliderPageStepAdd:
            step = self.duration // 10
        elif action == QAbstractSlider.SliderPageStepSub:
            step = -self.duration // 10
        else:
            return

        position = min(max(0, self.ui.tPosition.sliderPosition() + step), self.duration)
        self.player.set_position(position)
