# SPDX-License-Identifier: BSD-2-Clause
import app
import media
import util
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidgetItem


class Track:
    def __init__(self, track, index, skip=False):
        self.info = track
        self.skip = skip
        self.stop_after = False
        self.index = index


class Album(util.ConfigObj):
    K_SKIP_TRACKS = "skip"

    def __init__(self, album=None):
        self._info = album
        self._tracks = []
        self.path = None
        if album:
            self.path = album.path
            for i in range(len(album.tracks)):
                self.tracks.append(Track(album.tracks[i], i))

    @property
    def info(self):
        return self._info

    @property
    def tracks(self):
        return self._tracks

    def __getstate__(self):
        data = util.ConfigObj.__getstate__(self)
        data[self.K_SKIP_TRACKS] = [t.index for t in self._tracks if t.skip]
        return data

    def __setstate__(self, data):
        skip = data.get(self.K_SKIP_TRACKS, [])
        if skip:
            del data[self.K_SKIP_TRACKS]
        util.ConfigObj.__setstate__(self, data)

        self._info = app.get().collection.get_album(self.path)
        for i in range(len(self.info.tracks)):
            self._tracks.append(Track(self.info.tracks[i], i, skip=i in skip))


class Playlist(util.ConfigObj, util.Listener, util.EventSource):
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

        self.play(self.current_track())

    def play(self, track):
        self.track_idx = track.index
        if self._inhibity_play:
            self._player.set_track(track=track.info)
            self.fire_event(util.Listener.playlist_changed)
        else:
            self._player.play(track=track.info)
            self.fire_event(util.Listener.playlist_playing)

    def is_playing(self):
        return self._player.is_playing()

    def is_paused(self):
        return self._player.is_paused()

    def pause(self):
        self._player.pause()

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
        self.fire_event(util.Listener.playlist_changed)

        # TODO: show OSD that this happened

    def next(self):
        while True:
            album = self.albums[0]
            if self.track_idx < len(album.tracks) - 1:
                self.track_idx += 1
                if album.tracks[self.track_idx].skip:
                    continue
                self.play(self.current_track())
                return

            del self.albums[0]
            if not self.albums:
                self.fire_event(util.Listener.playlist_ended)
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
        self.fire_event(util.Listener.playlist_changed)
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
        self._inhibity_play = track.stop_after

        if track.stop_after:
            track.stop_after = False
            self._player.stop(fire_event=False)

        self.next()
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

        adapter = UIAdapter(ui)
        self.add_listener(adapter)
        ui.add_listener(adapter)
        self._player.init_ui(ui)

    def player(self):
        return self._player

    def add_album(self, album):
        self.albums.append(Album(album))
        self.fire_event(util.Listener.playlist_changed)

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

        self.fire_event(util.Listener.playlist_changed)


class AlbumUI(util.compile_ui("album.ui")):
    def __init__(self, parent, album):
        super().__init__(parent)
        self.album = album
        self.lArtist.setText(album.info.artist)
        self._album_helper = util.ElisionHelper(
            self, self.lAlbum, album.info.title, 128
        )
        self.lYear.setText(str(album.info.year))


class TrackUI(util.compile_ui("track.ui")):
    def __init__(self, ui, track):
        super().__init__(ui.playlistUI)
        self.track = track
        self.ui = ui
        self._title_helper = util.ElisionHelper(
            self, self.lTitle, f"{track.info.trackno} - {track.info.title}", 96
        )
        self.lDuration.setText(util.ms_to_text(track.info.duration_ms))
        self.set_playing(False)
        self.update()

    def set_playing(self, playing):
        icon = "play.png" if playing else "empty.png"
        util.set_pixmap(self.lPlaying, app.get().pixmaps.get_icon(icon))

    def update(self):
        font = self.lTitle.font()
        font.setItalic(self.track.skip)
        self.lTitle.setFont(font)

        icon = "stop.png" if self.track.stop_after else "empty.png"
        util.set_pixmap(self.lStopAfter, app.get().pixmaps.get_icon(icon))


class UIAdapter:
    def __init__(self, ui):
        self.ui = ui
        self._cover_img = None

        if app.get().playlist.albums:
            self._update_playlist()

        track = app.get().playlist.current_track()
        if track:
            self._update_track(track)

        self.ui.playlistUI.itemDoubleClicked.connect(self._play_item)

        self._playlist_released_key = self.ui.playlistUI.keyReleaseEvent
        self.ui.playlistUI.keyReleaseEvent = self._handle_key_released

    def track_playing(self, track):
        self._update_track(app.get().playlist.current_track())

    def playlist_changed(self):
        self._update_playlist()

    def ui_resized(self, widget):
        self._update_cover()

    def _update_track(self, track):
        self.ui.plArtist.setText(track.info.artist)
        self.ui.plAlbum.setText(track.info.album)
        self.ui.plYear.setText(str(track.info.year))

        idx = track.index + 1
        for i in range(self.ui.playlistUI.count()):
            item = self.ui.playlistUI.item(i)
            widget = self.ui.playlistUI.itemWidget(item)
            if isinstance(widget, TrackUI):
                widget.set_playing(i == idx)

    def _update_playlist(self):
        self.ui.playlistUI.clear()

        first = True
        for a in app.get().playlist.albums:
            album_ui = AlbumUI(self.ui.playlistUI, a)

            self._add_list_item(album_ui)

            for t in a.tracks:
                track_ui = TrackUI(self.ui, t)
                self._add_list_item(track_ui)

            cover = app.get().pixmaps.get_cover(a)
            if first:
                self._cover_img = cover
                self._update_cover()
                first = False

            util.set_pixmap(album_ui.cover, cover)

        self._update_track(app.get().playlist.current_track())

    def _update_cover(self):
        if self._cover_img:
            util.set_pixmap(self.ui.plCover, self._cover_img)

    def _add_list_item(self, widget):
        item = QListWidgetItem(self.ui.playlistUI)
        item.setSizeHint(widget.sizeHint())
        self.ui.playlistUI.addItem(item)
        self.ui.playlistUI.setItemWidget(item, widget)

    def _play_item(self, item):
        track = self.ui.playlistUI.itemWidget(item).track
        while track.info.album != app.get().playlist.albums[0].info.title:
            app.get().playlist.remove_album(app.get().playlist.albums[0])
        app.get().playlist.play(track)

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
                    app.get().playlist.remove_album(widget.album)
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

        app.get().playlist.stop_after(widget.track)
        self._update_playlist()
