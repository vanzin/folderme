# SPDX-License-Identifier: BSD-2-Clause
import collection
import lastfm
import playlist
import sys
import util
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

_INSTANCE = None


def init(args):
    global _INSTANCE
    _INSTANCE = FolderME(args)


def get():
    return _INSTANCE


class FolderME(QApplication):
    def __init__(self, args):
        QApplication.__init__(self, sys.argv)
        self.setWindowIcon(QIcon(util.icon("folderme.png")))

        self._pixmaps = util.PixmapCache()
        self._collection = util.load_config(collection.Collection)
        self._playlist = util.load_config(playlist.Playlist)
        self._scrobbler = lastfm.get_scrobbler(not args.no_lastfm)
        if self._scrobbler:
            self.playlist.add_listener(self._scrobbler)

    @property
    def pixmaps(self):
        return self._pixmaps

    @property
    def collection(self):
        return self._collection

    @property
    def playlist(self):
        return self._playlist

    def save(self):
        self.playlist.save()

    def exit(self):
        self.save()
        if self._scrobbler:
            self._scrobbler.shutdown()
        self.quit()
