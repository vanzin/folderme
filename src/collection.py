# SPDX-License-Identifier: BSD-2-Clause
import os

import mutagen
import util
from PySide6.QtCore import QThread
from PySide6.QtCore import Signal
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4Tags
from mutagen.id3 import ID3
from mutagen.mp4 import MP4Tags

METADATA_VERSION = 5


class Track(util.ConfigObj):
    def __init__(self):
        self.path = None
        self.artist = None
        self.album = None
        self.title = None
        self.duration_ms = 0
        self.trackno = -1
        self.year = -1
        self.skip = False
        self._discno = None

    def init(self, path):
        mf = mutagen.File(path, easy=True)
        if not mf:
            raise Exception(f"Unrecognized file {path}")

        if type(mf.tags) not in [EasyID3, EasyMP4Tags]:
            raise Exception(f"Don't know how to handle {type(mf.tags)}")

        self.path = path
        self._read_id3(mf, mf.tags)

    def _read_id3(self, f, tags):
        self.artist = tags["artist"][0]
        self.album = tags["album"][0]
        self.title = tags["title"][0]
        try:
            self.year = int(tags["date"][0])
        except:
            print(f"track {self.path} is missing date information")

        # Some tracks show up as "x/y" and some as just "x". Don't know why.
        parts = tags["tracknumber"][0].split("/")
        self.trackno = int(parts[0])

        self._discno = 1
        try:
            discno = tags["discnumber"][0]
            self._discno = int(discno.split("/")[0])
        except:
            pass

        self.duration_ms = int(f.info.length * 1000)

    def cover_art(self):
        if not self.path or not os.path.isfile(self.path):
            return None
        tags = mutagen.File(self.path).tags
        if type(tags) == ID3:
            for candidate in ["APIC:", "APIC:cover"]:
                art = tags.get(candidate)
                if art:
                    art = art.data
                    break
        elif type(tags) == MP4Tags:
            art = tags.get("aART")
            if not art:
                art = tags.get("covr")
            if isinstance(art, list):
                art = art[0]

        return art

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
        discnos = set()

        if not files:
            files = [
                x for x in os.listdir(path) if os.path.isfile(os.path.join(path, x))
            ]

        for f in files:
            t = Track()
            try:
                t.init(os.path.join(path, f))
            except Exception:
                continue

            if title and title != t.album:
                raise Exception(f"Inconsistent album info in {path}.")

            title = t.album
            year = t.year
            if t._discno:
                discnos.add(t._discno)

            if artist is None:
                artist = t.artist
            elif t.artist.lower() != artist.lower():
                artist = "Various"

            mtime = max(mtime, os.stat(t.path).st_mtime)
            tracks.append(t)

        if not artist:
            raise Exception(f"Unable to figure out path {path}")

        tracks.sort(key=lambda x: (x._discno or -1, x.trackno, x.path))

        if len(discnos) == 1:
            in_set = False
            discno = list(discnos)[0]
            try:
                discno = int(discno)
                in_set = discno > 1
            except:
                parts = discno.split("/")
                discno = int(parts[0])
                in_set = int(parts[1]) > 1

            if in_set and not title.endswith(f"(Disc {discno})"):
                title = f"{title} (Disc {discno})"
                for track in tracks:
                    track.album = title

        self.title = title
        self.artist = artist
        self.tracks = tracks
        self.year = year
        self.mtime = mtime
        self.version = METADATA_VERSION

    def __str__(self):
        return "Album({})".format(str(self.__dict__))


class Scanner(QThread):
    progress = Signal(str)
    done = Signal()

    def __init__(self, collection):
        QThread.__init__(self)
        self.collection = collection

    def run(self):
        albums = []
        for path in self.collection.locations:
            for root, dirs, files, dirfd in os.fwalk(path):
                self.progress.emit(root)
                if files:
                    a = self.collection.get_album(root)
                    if a and a.version == METADATA_VERSION:
                        mtime = max(os.stat(f, dir_fd=dirfd).st_mtime for f in files)
                        if mtime <= a.mtime:
                            albums.append(a)
                            continue

                    try:
                        a = Album()
                        a.init(root, files=files)
                        albums.append(a)
                    except:
                        pass

        self.collection.albums = albums
        self.done.emit()


class ScanDialog(util.compile_ui("rescan.ui")):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lScanState.setText("Scanning...")

    def scan_progress(self, path):
        self.lScanState.setText(f"Scanning {path}...")


class Collection(util.ConfigObj):
    def __init__(self):
        self.albums = []
        self.locations = []
        self.version = -1
        self._scanner = None
        self._by_path = None

    def needs_rescan(self):
        return self.version != METADATA_VERSION

    def scan(self, parent=None):
        dlg = ScanDialog(parent)
        if self._scanner:
            raise Exception("Scanning already in progress.")

        self._scanner = Scanner(self)
        self._scanner.done.connect(self.scan_done)
        self._scanner.done.connect(dlg.close)
        self._scanner.progress.connect(dlg.scan_progress)
        self._scanner.start()
        dlg.exec()

    def scan_done(self):
        self.version = METADATA_VERSION
        self.save()
        self._scanner = None
        util.EventBus.send(util.Listener.collection_changed)

    def get_album(self, path):
        if not self._by_path:
            self._by_path = {x.path: x for x in self.albums}
        return self._by_path.get(path)
