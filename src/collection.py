# SPDX-License-Identifier: BSD-2-Clause
import mutagen
import os
import util
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from PyQt5.QtCore import QObject, QThread, pyqtSignal

METADATA_VERSION = 2


class Track(util.ConfigObj):
    def __init__(self):
        self.path = None
        self.artist = None
        self.album = None
        self.title = None
        self.duration_ms = 0
        self.trackno = -1
        self.year = -1

    def init(self, path):
        mf = mutagen.File(path, easy=True)
        if not mf:
            raise Exception(f"Unrecognized file {path}")

        if type(mf.tags) != EasyID3:
            raise Exception(f"Don't know how to handle {type(mf.tags)}")

        self.path = path
        self._read_id3(mf, mf.tags)

    def _read_id3(self, f, tags):
        self.artist = tags["artist"][0]
        self.album = tags["album"][0]
        self.title = tags["title"][0]
        self.year = tags["date"][0]

        # Some tracks show up as "x/y" and some as just "x". Don't know why.
        parts = tags["tracknumber"][0].split("/")
        self.trackno = int(parts[0])

        self.duration_ms = int(f.info.length * 1000)

    def cover_art(self):
        tags = ID3(self.path)
        art = tags.get("APIC:")
        return art.data if art else None

    def info(self):
        f = mutagen.File(self.path, easy=True)
        return (f.info, f.tags)

    def __str__(self):
        return "Track({})".format(str(self.__dict__))


class Album(util.ConfigObj):
    def __init__(self):
        self.path = None
        self.title = None
        self.artist = None
        self.tracks = []
        self.mtime = 0
        self.year = -1
        self.version = -1

    def init(self, path, files=None):
        self.path = path

        artist = None
        title = None
        mtime = 0
        tracks = []
        year = -1

        if not files:
            files = [
                x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))
            ]

        for f in files:
            t = Track()
            t.init(os.path.join(path, f))
            if title and title != t.album:
                raise Exception(f"Inconsistent album info in {path}.")

            title = t.album
            year = t.year

            if artist is None:
                artist = t.artist
            elif t.artist.lower() != artist.lower():
                artist = "Various"

            mtime = max(mtime, os.stat(t.path).st_mtime)
            tracks.append(t)

        if not artist:
            raise Exception(f"Unable to figure out path {path}")

        tracks.sort(key=lambda x: x.path)

        self.title = title
        self.artist = artist
        self.tracks = tracks
        self.year = year
        self.mtime = mtime
        self.version = METADATA_VERSION

    def __str__(self):
        return "Album({})".format(str(self.__dict__))


class ScanListener:
    def scan_progress(self, path):
        pass

    def scan_done(self):
        pass


class Scanner(QThread, util.EventSource):
    progress = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, collection):
        QThread.__init__(self)
        util.EventSource.__init__(self)
        self.collection = collection

    def run(self):
        albums = []
        by_path = {x.path: x for x in self.collection.albums}
        for path in self.collection.locations:
            for root, dirs, files, dirfd in os.fwalk(path):
                self.progress.emit(root)
                if files:
                    a = by_path.get(root)
                    if a and a.version == METADATA_VERSION:
                        mtime = min(os.stat(f, dir_fd=dirfd).st_mtime for f in files)
                        if mtime <= a.mtime:
                            albums.append(a)
                            continue

                    try:
                        a = Album()
                        a.init(root, files=files)
                        albums.append(a)
                        tcnt += len(a.tracks)
                    except:
                        pass

        self.collection.albums = albums
        self.done.emit()


class Collection(util.ConfigObj, util.EventSource):
    def __init__(self):
        util.EventSource.__init__(self)
        self.albums = []
        self.locations = []
        self._scanner = None

    def scan(self, listener=None):
        if self._scanner:
            raise Exception("Scanning already in progress.")

        self._scanner = Scanner(self)
        self._scanner.done.connect(self.scan_done)
        if listener:
            self._scanner.progress.connect(listener.scan_progress)
            self._scanner.done.connect(listener.scan_done)
        self._scanner.start()

    def scan_done(self):
        self._scanner = None
        self.fire_event(util.Listener.collection_changed)
