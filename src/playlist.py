# SPDX-License-Identifier: BSD-2-Clause
import media
import util


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
        self.current_track = 0
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

        track = self.albums[0].tracks[self.current_track]
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
        if self.current_track < len(album.tracks) - 1:
            self.current_track += 1
            self.playpause()
            return

        del self.albums[0]
        if self.albums:
            self.current_track = 0
            self.playpause()
            self.fire_event(Listener.playlist_changed, self)
        else:
            self.fire_event(Listener.playlist_ended, self)

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

    def add_listener(self, l):
        util.EventSource.add_listener(self, l)
        self._player.add_listener(l)

    def track_ended(self, player):
        self.next()
