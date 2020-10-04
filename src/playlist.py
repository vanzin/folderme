# SPDX-License-Identifier: BSD-2-Clause
import media
import util
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QListWidgetItem,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QWidget,
)


class Listener:
    def playlist_playing(self, playlist):
        pass

    def playlist_changed(self, playlist):
        pass

    def playlist_ended(self, playlist):
        pass


class Track:
    def __init__(self, track):
        self.info = track
        self.skip = False
        self.stop_after = False


class Album:
    def __init__(self, album):
        self.info = album
        self.tracks = [Track(t) for t in album.tracks]


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
        self._player.play(track=track.info)
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
        self.albums.append(Album(album))

    def replace(self, album, play=False):
        play = play or self.is_playing()
        self.albums = [Album(album)]
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
        track = self.current_track()
        if not track.stop_after:
            self.next()
            return

        self.stop()
        if self.track_idx == len(album.tracks) - 1:
            self.fire_event(Listener.playlist_ended, self)

    def init_ui(self, ui):
        adapter = UIAdapter(ui, self)
        self.add_listener(adapter)
        ui.add_listener(adapter)
        self._player.init_ui(ui)


class AlbumUI(QWidget):
    def __init__(self, parent, album):
        QWidget.__init__(self, parent)
        util.init_ui(self, "album.ui")
        self.lArtist.setText(album.info.artist)
        self.lAlbum.setText(album.info.title)


class TrackUI(QWidget):
    def __init__(self, parent, track):
        QWidget.__init__(self, parent)
        util.init_ui(self, "track.ui")

        info = track.info
        self.lTitle.setText(f"{info.trackno} - {info.title}")
        self.lDuration.setText(util.ms_to_text(info.duration_ms))
        self.set_playing(False)

    def set_playing(self, playing):
        pixmap = QPixmap()
        if playing:
            pixmap.load(util.icon("play.png"))
        else:
            pixmap.load(util.icon("empty.png"))
        util.set_pixmap(self.lPlaying, pixmap)


class UIAdapter:
    def __init__(self, ui, playlist):
        self.ui = ui
        self.playlist = playlist
        self._cover_img = None

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
        self.ui.plArtist.setText(track.info.artist)
        self.ui.plAlbum.setText(track.info.album)

        idx = 0
        for t in self.playlist.albums[0].tracks:
            idx += 1
            if t is track:
                break

        for i in range(self.ui.playlistUI.count()):
            item = self.ui.playlistUI.item(i)
            widget = self.ui.playlistUI.itemWidget(item)
            if isinstance(widget, TrackUI):
                widget.set_playing(i == idx)

    def _update_playlist(self, playlist):
        self.ui.playlistUI.clear()

        first = True
        for a in playlist.albums:
            album_ui = AlbumUI(self.ui.playlistUI, a)

            self._add_list_item(album_ui)

            cover = None
            for t in a.tracks:
                track_ui = TrackUI(self.ui.playlistUI, t)
                self._add_list_item(track_ui)
                if not cover:
                    cover = t.info.cover_art()

            pixmap = QPixmap()
            if cover:
                pixmap.loadFromData(cover)
            else:
                pixmap.load(util.icon("blank.jpg"))

            self._cover_img = pixmap

            if first:
                self._update_cover()
                first = False
            util.set_pixmap(album_ui.cover, pixmap)

        self._update_track(self.playlist.current_track())

    def _update_cover(self):
        if self._cover_img:
            util.set_pixmap(self.ui.plCover, self._cover_img)

    def _add_list_item(self, widget):
        item = QListWidgetItem(self.ui.playlistUI)
        item.setSizeHint(widget.sizeHint())
        self.ui.playlistUI.addItem(item)
        self.ui.playlistUI.setItemWidget(item, widget)
