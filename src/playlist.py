# SPDX-License-Identifier: BSD-2-Clause
import media
import util
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem


class Listener:
    def playlist_playing(self, playlist):
        pass

    def playlist_changed(self, playlist):
        pass

    def playlist_ended(self, playlist):
        pass


class Playlist(util.ConfigObj, media.Listener, util.EventSource):
    def __init__(self):
        util.EventSource.__init__(self)
        self.albums = []
        self.track_idx = 0
        self._player = media.Player()
        self._player.add_listener(self)

    def playpause(self):
        if self._player.is_playing():
            self._player.pause()
            return

        if self._player.is_paused():
            self._player.play()
            return

        if not self.albums:
            print("no albums")
            return

        track = self.albums[0].tracks[self.track_idx]
        print(f"start {track}")
        self._player.play(track=track)
        self.fire_event(Listener.playlist_playing, self)

    def is_playing(self):
        return self._player.is_playing()

    def stop(self):
        self._player.stop()

    def next(self):
        self.stop()

        album = self.albums[0]
        if self.track_idx < len(album.tracks) - 1:
            self.track_idx += 1
            self.playpause()
            return

        del self.albums[0]
        if self.albums:
            self.track_idx = 0
            self.playpause()
            self.fire_event(Listener.playlist_changed, self)
        else:
            self.fire_event(Listener.playlist_ended, self)

    def prev(self):
        self.stop()
        if self.track_idx > 0:
            self.track_idx -= 1
        self.playpause()

    def add(self, album):
        self.albums.append(album)

    def replace(self, album, play=False):
        play = play or self.is_playing()
        self.albums = [album]
        self.track_idx = 0
        self.stop()
        self.fire_event(Listener.playlist_changed, self)
        if play:
            self.playpause()

    def current_track(self):
        if not self.albums:
            return None
        return self.albums[0].tracks[self.track_idx]

    def add_listener(self, l):
        util.EventSource.add_listener(self, l)
        self._player.add_listener(l)

    def track_ended(self, player):
        self.next()


class UIAdapter:
    def __init__(self, ui, playlist):
        self.ui = ui
        self.playlist = playlist
        self._cover_img = None
        ui.add_listener(self)

        if playlist.albums:
            self._update_playlist(self.playlist)

        track = playlist.current_track()
        if track:
            self._update_track(track)

    def track_playing(self, player):
        self._update_track(self.playlist.current_track())

    def playlist_changed(self, playlist):
        self._update_playlist(playlist)

    def ui_resized(self, widget):
        self._update_cover()

    def ui_exit(self):
        util.save_config(self.playlist)

    def _update_track(self, track):
        self.ui.plArtist.setText(track.artist)
        self.ui.plAlbum.setText(track.album)

    def _update_playlist(self, playlist):
        self.ui.playlistUI.clear()

        for a in playlist.albums:
            self.ui.playlistUI.addItem(f"{a.artist} / {a.title}")

            cover = a.tracks[0].cover_art()
            if cover:
                pixmap = QPixmap()
                pixmap.loadFromData(cover)
                self._cover_img = pixmap
                self._update_cover()

            for t in a.tracks:
                self.ui.playlistUI.addItem(f"  {t.title}")

    def _update_cover(self):
        if not self._cover_img:
            return

        cover = QGraphicsPixmapItem(self._cover_img)
        scene = QGraphicsScene(self.ui.plCover)
        scene.addItem(cover)
        self.ui.plCover.setScene(scene)
        self.ui.plCover.fitInView(cover, Qt.KeepAspectRatio)
