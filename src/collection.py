# SPDX-License-Identifier: BSD-2-Clause
import mutagen
import os
import util
from mutagen.easyid3 import EasyID3


class Track:
    def __init__(self, path):
        mf = mutagen.File(path, easy=True)
        if not mf:
            raise Exception(f"Unrecognized file {path}")

        if type(mf.tags) != EasyID3:
            raise Exception(f"Don't know how to handle {type(mf.tags)}")

        self.path = path
        self._read_id3(mf.tags)

    def _read_id3(self, tags):
        self.artist = tags["artist"][0]
        self.album = tags["album"][0]
        self.title = tags["title"]

    def __str__(self):
        return "Track({})".format(str(self.__dict__))


class Album:
    def __init__(self, path, files=None):
        self.path = path

        artist = None
        album = None
        mtime = 0
        tracks = []

        if not files:
            files = [
                x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))
            ]

        for f in files:
            t = Track(os.path.join(path, f))
            if album and album != t.album:
                raise Exception(f"Inconsistent album info in {path}.")

            album = t.album

            if artist is None:
                artist = t.artist
            elif t.artist.lower() != artist.lower():
                artist = "Various"

            mtime = max(mtime, os.stat(t.path).st_mtime)
            tracks.append(t)

        if not artist:
            raise Exception(f"Unable to figure out path {path}")

        self.album = album
        self.artist = artist
        self.tracks = tracks
        self.mtime = mtime

    def __str__(self):
        return "Album({})".format(str(self.__dict__))


class Collection:
    def __init__(self):
        self.albums = []
        self.locations = ["/media/common/music"]

    def scan(self):
        albums = []
        tcnt = 0
        for path in self.locations:
            for root, dirs, files in os.walk(path):
                if files:
                    try:
                        a = Album(root, files=files)
                        albums.append(a)
                        tcnt += len(a.tracks)
                    except:
                        pass

        self.albums = albums

    def random(self):
        pass
