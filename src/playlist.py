# SPDX-License-Identifier: BSD-2-Clause
import media
import util


class Listener:
    def playlist_changed(self, playlist):
        pass

    def playlist_ended(self, playlist):
        pass


class PlayerListener(media.Listener):
    def __init__(self, playlist):
        self.playlist = playlist

    def ended(self, player):
        self.playlist.next()


class Playlist(util.ConfigObj):
    def __init__(self):
        self.albums = []
        self.current_track = 0
        self._player_listener = PlayerListener(self)
        self._listeners = []
        self._player = media.Player(self._player_listener)

    def add_listener(self, l):
        self._listeners.append(l)

    def playpause(self):
        if self._player.is_playing():
            self._player.pause()
            return

        if not self.albums:
            print("no albums")
            return

        track = self.albums[0].tracks[self.current_track]
        print(f"start {track}")
        self._player.play(track=track)

    def is_playing(self):
        return self._player.is_playing()

    def stop(self):
        self._player.stop()

    def next(self):
        self.stop()

        album = self.albums[0]
        if self.current_track < len(album.tracks) - 1:
            self.current_track += 1
            self.playpause()
            return

        del self.albums[0]
        if self.albums:
            self.current_track = 0
            self.playpause()
            for l in self._listeners:
                l.playlist_changed(self)
        else:
            for l in self._listeners:
                l.playlist_ended(self)

    def prev(self):
        self.stop()
        if self.current_track > 0:
            self.current_track -= 1
        self.playpause()

    def add(self, album):
        self.albums.append(album)

    def replace(self, album, play=False):
        play = play or self.is_playing()
        self.albums = [album]
        self.current_track = 0
        self.stop()
        if play:
            self.playpause()
