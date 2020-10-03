# SPDX-License-Identifier: BSD-2-Clause
import media
import util
from PyQt5.QtCore import Qt
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

    def init_ui(self, ui):
        adapter = UIAdapter(ui, self)
        self.add_listener(adapter)
        ui.add_listener(adapter)
        self._player.init_ui(ui)


class AlbumUI(QWidget):
    def __init__(self, parent, album):
        QWidget.__init__(self, parent)
        util.init_ui(self, "album.ui")
        self.lArtist.setText(album.artist)
        self.lAlbum.setText(album.title)


class TrackUI(QWidget):
    def __init__(self, parent, track):
        QWidget.__init__(self, parent)
        util.init_ui(self, "track.ui")

        info, tags = track.info()
        duration = int(info.length * 1000)
        title = tags["title"][0]
        trackno = tags["tracknumber"][0]

        self.lTitle.setText(f"{trackno} - {title}")
        self.lDuration.setText(util.ms_to_text(duration))


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
        self.ui.plArtist.setText(track.artist)
        self.ui.plAlbum.setText(track.album)

    def _update_playlist(self, playlist):
        self.ui.playlistUI.clear()

        for a in playlist.albums:
            album_ui = AlbumUI(self.ui.playlistUI, a)

            self._add_list_item(album_ui)

            cover = None
            for t in a.tracks:
                track_ui = TrackUI(self.ui.playlistUI, t)
                self._add_list_item(track_ui)
                if not cover:
                    cover = t.cover_art()

            pixmap = QPixmap()
            if cover:
                pixmap.loadFromData(cover)
            else:
                pixmap.load(util.icon("blank.jpg"))

            self._cover_img = pixmap

            self._update_cover()
            self._set_pixmap(album_ui.cover, pixmap)

        self._update_track(self.playlist.current_track())

    def _update_cover(self):
        self._set_pixmap(self.ui.plCover, self._cover_img)

    def _set_pixmap(self, label, pixmap):
        if pixmap:
            h = label.height() - 5
            w = label.width() - 5
            scaled = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
        else:
            label.setPixmap(None)

    def _add_list_item(self, widget):
        item = QListWidgetItem(self.ui.playlistUI)
        item.setSizeHint(widget.sizeHint())
        self.ui.playlistUI.addItem(item)
        self.ui.playlistUI.setItemWidget(item, widget)
