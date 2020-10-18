# SPDX-License-Identifier: BSD-2-Clause
import sys

import collection
import lastfm
import playlist
import util
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

_INSTANCE = None


def init(args):
    global _INSTANCE
    _INSTANCE = FolderME()
    _INSTANCE.init(args)


def get():
    return _INSTANCE


class FolderME(QApplication):
    def __init__(self):
        QApplication.__init__(self, sys.argv)
        self.setWindowIcon(QIcon(util.icon("folderme.png")))

    def init(self, args):
        self._pixmaps = util.PixmapCache()
        self._collection = collection.Collection.load()
        self._playlist = playlist.Playlist.load()
        self._scrobbler = lastfm.get_scrobbler(not args.no_lastfm)
        if self._scrobbler:
            self.playlist.add_listener(self._scrobbler)

        self._bias = 1

        bias = util.SETTINGS.value("playlist/bias")
        if bias:
            self._bias = int(bias)

    @property
    def pixmaps(self):
        return self._pixmaps

    @property
    def collection(self):
        return self._collection

    @property
    def playlist(self):
        return self._playlist

    @property
    def bias(self):
        return self._bias

    def set_bias(self, bias):
        self._bias = bias

    def save(self):
        self.playlist.save()

    def exit(self):
        self.save()
        if self._scrobbler:
            self._scrobbler.shutdown()
        self.quit()
