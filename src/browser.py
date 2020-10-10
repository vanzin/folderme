# SPDX-License-Identifier: BSD-2-Clause
import collections
import util
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QWidget


class AlbumEntry(QWidget):
    def __init__(self, album):
        QWidget.__init__(self)
        util.init_ui(self, "browser_album.ui")
        self.album = album

        cover = album.tracks[0].cover_art()
        pixmap = QPixmap()
        if cover:
            pixmap.loadFromData(cover)
        else:
            pixmap.load(util.icon("blank.jpg"))

        util.set_pixmap(self.cover, pixmap)
        self.lAlbum.setText(album.title)
        self.lYear.setText(str(album.year))


class BrowseDialog(QDialog):
    def __init__(self, parent, collection):
        QDialog.__init__(self, parent)
        util.init_ui(self, "browser.ui")
        self.bRescan.clicked.connect(self._rescan)
        self.bClose.clicked.connect(self.close)
        self.collection = collection
        self._scanning = False
        self._populate_artists()
        util.restore_ui(self, "browser")

    def closeEvent(self, e):
        util.save_ui(self, "browser")
        QDialog.closeEvent(self, e)

    def _populate_artists(self):
        self.artists_map = collections.defaultdict(list)
        for a in self.collection.albums:
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

        self.artists.itemActivated.connect(self._populate_albums)
        self.repaint()

    def _populate_albums(self, item):
        self.albums.clear()
        albums = self.artists_map.get(item.text())

        for a in albums:
            ui = AlbumEntry(a)
            i = QListWidgetItem(self.albums)
            i.setFlags(i.flags() & ~Qt.ItemIsSelectable)
            i.setSizeHint(ui.sizeHint())
            self.albums.addItem(i)
            self.albums.setItemWidget(i, ui)

    def _rescan(self):
        self.collection.scan()
        util.save_config(self.collection)
        self.artists.clear()
        self.albums.clear()
        self._populate_artists()
