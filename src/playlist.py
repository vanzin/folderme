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


class Track:
    def __init__(self, track, index):
        self.info = track
        self.skip = False
        self.stop_after = False
        self.index = index


class Album:
    def __init__(self, album):
        self.info = album
        self.tracks = []
        for i in range(len(album.tracks)):
            self.tracks.append(Track(album.tracks[i], i))


class Playlist(util.ConfigObj, media.Listener, util.EventSource):
    def __init__(self):
        util.EventSource.__init__(self)
        self.albums = []
        self.track_idx = 0
        self._player = media.Player()
        self._player.add_listener(self)
        self._inhibity_play = False

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

        self.play(self.albums[0].tracks[self.track_idx])

    def play(self, track):
        if not self._inhibity_play:
            self.track_idx = track.index
            self._player.play(track=track.info)
            self.fire_event(Listener.playlist_playing, self)

    def is_playing(self):
        return self._player.is_playing()

    def stop(self):
        self._player.stop()

    def stop_after(self, track):
        new_value = not track.stop_after
        valid = True
        for a in self.albums:
            idx = 0
            for t in a.tracks:
                t.stop_after = False
                if new_value and t is track and idx < self.track_idx:
                    # Stop after for a previous track does not make sense. Ignore the
                    # call.
                    new_value = False
                idx += 1
        track.stop_after = new_value

    def next(self):
        while True:
            album = self.albums[0]
            if self.track_idx < len(album.tracks) - 1:
                self.track_idx += 1
                if album.tracks[self.track_idx].skip:
                    continue
                self.playpause()
                return

            del self.albums[0]
            if not self.albums:
                self.fire_event(Listener.playlist_ended, self)
                return

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

    def track_ended(self, _):
        track = self.current_track()
        if not track.stop_after:
            self.stop()
            self.next()
            return

        if self.track_idx == len(self.albums[0].tracks) - 1:
            del self.albums[0]
            self._inhibity_play = True
            self.fire_event(Listener.playlist_ended, self)
            self._inhibity_play = False

    def init_ui(self, ui):
        track = self.current_track()
        if track:
            self._player.set_track(track.info)

        if self.albums:
            first = self.albums[0]
            for i in range(len(first.tracks)):
                if first.tracks[i].stop_after and i != self.track_idx:
                    first.tracks[i].stop_after = False

        adapter = UIAdapter(ui, self)
        self.add_listener(adapter)
        ui.add_listener(adapter)
        self._player.init_ui(ui)

    def player(self):
        return self._player

    def add_album(self, album):
        self.albums.append(Album(album))
        self.fire_event(Listener.playlist_changed, self)

    def remove_album(self, album):
        stop = False
        for i in range(len(self.albums)):
            a = self.albums[i]
            if a is album:
                stop = i == 0
                del self.albums[i]
                break

        if stop:
            play = self.is_playing()
            self.stop()
            self.track_idx = 0
            if play:
                self.playpause()

        self.fire_event(Listener.playlist_changed, self)


class AlbumUI(QWidget):
    def __init__(self, parent, album):
        QWidget.__init__(self, parent)
        util.init_ui(self, "album.ui")
        self.album = album
        self.lArtist.setText(album.info.artist)
        self.lAlbum.setText(album.info.title)


class TrackUI(QWidget):
    def __init__(self, parent, track):
        QWidget.__init__(self, parent)
        util.init_ui(self, "track.ui")
        self.track = track

        info = track.info
        self.lTitle.setText(f"{info.trackno} - {info.title}")
        self.lDuration.setText(util.ms_to_text(info.duration_ms))
        self.set_playing(False)

        pixmap = QPixmap()
        if track.stop_after:
            pixmap.load(util.icon("stop.png"))
        else:
            pixmap.load(util.icon("empty.png"))
        util.set_pixmap(self.lStopAfter, pixmap)

    def set_playing(self, playing):
        pixmap = QPixmap()
        if playing:
            pixmap.load(util.icon("play.png"))
        else:
            pixmap.load(util.icon("empty.png"))
        util.set_pixmap(self.lPlaying, pixmap)

    def update(self):
        font = self.lTitle.font()
        font.setItalic(self.track.skip)
        self.lTitle.setFont(font)
        self.repaint()


class UIAdapter:
    def __init__(self, ui, playlist):
        self.ui = ui
        self.playlist = playlist
        self._cover_img = None

        if playlist.albums:
            self._update_playlist()

        track = playlist.current_track()
        if track:
            self._update_track(track)

        self.ui.playlistUI.itemDoubleClicked.connect(self._play_item)

        self._playlist_released_key = self.ui.playlistUI.keyReleaseEvent
        self.ui.playlistUI.keyReleaseEvent = self._handle_key_released

    def track_playing(self, track):
        self._update_track(self.playlist.current_track())

    def playlist_changed(self, playlist):
        self._update_playlist()

    def ui_resized(self, widget):
        self._update_cover()

    def ui_exit(self):
        util.save_config(self.playlist)

    def _update_track(self, track):
        self.ui.plArtist.setText(track.info.artist)
        self.ui.plAlbum.setText(track.info.album)

        idx = track.index + 1
        for i in range(self.ui.playlistUI.count()):
            item = self.ui.playlistUI.item(i)
            widget = self.ui.playlistUI.itemWidget(item)
            if isinstance(widget, TrackUI):
                widget.set_playing(i == idx)

        self.ui.playlistUI.repaint()

    def _update_playlist(self):
        self.ui.playlistUI.clear()

        first = True
        for a in self.playlist.albums:
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

            if first:
                self._cover_img = pixmap
                self._update_cover()
                first = False

            util.set_pixmap(album_ui.cover, pixmap)

        self._update_track(self.playlist.current_track())
        self.ui.playlistUI.repaint()

    def _update_cover(self):
        if self._cover_img:
            util.set_pixmap(self.ui.plCover, self._cover_img)

    def _add_list_item(self, widget):
        item = QListWidgetItem(self.ui.playlistUI)
        item.setSizeHint(widget.sizeHint())
        self.ui.playlistUI.addItem(item)
        self.ui.playlistUI.setItemWidget(item, widget)

    def _play_item(self, item):
        track_ui = self.ui.playlistUI.itemWidget(item)
        self.ui.playlist.play(track_ui.track)

    def _handle_key_released(self, event):
        if event.key() == Qt.Key_Delete:
            self._skip_selection(True)
        elif event.key() == Qt.Key_Plus:
            self._skip_selection(False)
        elif event.key() == Qt.Key_S:
            self._set_stop_after()
        else:
            self._playlist_released_key(event)

    def _skip_selection(self, skip):
        for item in self.ui.playlistUI.selectedItems():
            widget = self.ui.playlistUI.itemWidget(item)
            if isinstance(widget, AlbumUI):
                if skip:
                    self.playlist.remove_album(widget.album)
            else:
                widget.track.skip = skip
                widget.update()

    def _set_stop_after(self):
        items = self.ui.playlistUI.selectedItems()
        if len(items) != 1:
            return

        widget = self.ui.playlistUI.itemWidget(items[0])
        if not isinstance(widget, TrackUI):
            return

        self.playlist.stop_after(widget.track)
        self._update_playlist()
