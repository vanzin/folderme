# SPDX-License-Identifier: BSD-2-Clause
import app
import collections
import util
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QListWidgetItem


class AlbumEntry(util.compile_ui("browser_album.ui")):
    def __init__(self, parent, album):
        super().__init__(parent)
        self.album = album

        cover = album.tracks[0].cover_art()
        pixmap = QPixmap()
        if cover:
            pixmap.loadFromData(cover)
        else:
            pixmap.load(util.icon("blank.jpg"))

        util.set_pixmap(self.cover, pixmap)
        self._title_helper = util.ElisionHelper(self, self.lAlbum, album.title, 128)
        self.lYear.setText(str(album.year))


class BrowseDialog(util.compile_ui("browser.ui")):
    def __init__(self, parent):
        super().__init__(parent)
        self.bRescan.clicked.connect(self._rescan)
        self.bClose.clicked.connect(self.close)
        self.albums.itemActivated.connect(self._add_album)
        self.artists.itemActivated.connect(self._populate_albums)
        self._scanning = False
        self._populate_artists()
        util.restore_ui(self, "browser")

    def closeEvent(self, e):
        util.save_ui(self, "browser")
        super().closeEvent(e)

    def _add_album(self, item):
        e = self.albums.itemWidget(item)
        app.get().playlist.add_album(e.album)

    def _populate_artists(self):
        self.artists_map = collections.defaultdict(list)
        for a in app.get().collection.albums:
            self.artists_map[a.artist].append(a)

        for _, lst in self.artists_map.items():
            lst.sort(key=lambda a: a.year)

        names = list(self.artists_map.keys())

        def sort_key(name):
            if name == "Various":
                return (1, name.lower())
            return (0, name)

        names = sorted(names, key=sort_key)
        prev = None
        for n in names:
            first = n[0].lower()

            add_separator = False
            if prev == "#":
                try:
                    int(first)
                except:
                    add_separator = True
                    prev = first
            elif prev:
                add_separator = first != prev
                prev = first
            else:
                add_separator = True
                try:
                    int(first)
                    first = "#"
                    prev = first
                except:
                    prev = first

            if add_separator:
                i = QListWidgetItem(first.upper())
                i.setFlags(i.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                self.artists.addItem(i)

            i = QListWidgetItem(n)
            i.setFlags(i.flags() & ~Qt.ItemIsSelectable)
            self.artists.addItem(i)

        self.repaint()

    def _populate_albums(self, item):
        self.albums.clear()
        albums = self.artists_map.get(item.text())

        for a in albums:
            ui = AlbumEntry(self.albums, a)
            i = QListWidgetItem(self.albums)
            i.setFlags(i.flags() & ~Qt.ItemIsSelectable)
            i.setSizeHint(ui.sizeHint())
            self.albums.addItem(i)
            self.albums.setItemWidget(i, ui)

    def _rescan(self):
        app.get().collection.scan(self)

    def scan_done(self):
        self.artists.clear()
        self.albums.clear()
        self._populate_artists()
        self.bRescan.setEnabled(True)
        self.bClose.setEnabled(True)
