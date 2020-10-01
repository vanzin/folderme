# SPDX-License-Identifier: BSD-2-Clause
import media
import util


class Listener:
    def playlist_ended(self, playlist):
        pass


class PlayerListener(media.Listener):
    def __init__(self, playlist):
        self.playlist = playlist

    def stopped(self, player):
        self.playlist._player = None

    def ended(self, player):
        self.playlist._player = None
        self.playlist.next()


class Playlist(util.ConfigObj):
    def __init__(self):
        self.albums = []
        self.current_track = -1
        self._player_listener = PlayerListener(self)
        self._listeners = []
        self._player = None

    def add_listener(self, l):
        self._listeners.append(l)

    def playpause(self):
        if self._player and self._player.is_playing():
            self._player.pause()
            return

        if not self.albums:
            return

        track = self.albums[0].tracks[self.current_track]
        print(f"Starting track {track.path}")
        self._player = media.Player(track.path, self._player_listener)
        self._player.play()

    def stop(self):
        # TODO
        pass

    def next(self):
        # TODO
        pass

    def prev(self):
        # TODO
        pass

    def add(self, album):
        self.albums.append(album)

    def replace(self, album):
        self.stop()
        self.albums = [album]
        self.current_track = 0
