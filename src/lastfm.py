# SPDX-License-Identifier: BSD-2-Clause
import hashlib
import http
import os
import re
import sys
import threading
import time
from xml.dom import minidom

import requests
import util

API_KEY = "d6011cfd9d9a3bdedb3c3980e9cdab0e"
SECRET = "353fa1593215d359123dc209c4101da8"
API_URL = "https://ws.audioscrobbler.com/2.0/"

SETTINGS_GRP = "last.fm"
SETTINGS_SESSION_KEY = "session_key"

MULTI_DISC_RE = re.compile(r"(.*)\s+\(Disc [0-9]+\)")


def _check_response(res):
    if res.status_code != http.HTTPStatus.OK:
        raise Exception(f"Error: {res.status_code} {res.text}")


class Scrobble:
    def __init__(self):
        self.artist = None
        self.album = None
        self.timestamp = None
        self.is_ended = False
        self.start_time = None


class ScrobbleCache(util.ConfigObj):
    def __init__(self):
        self.scrobbles = []

    def is_empty(self):
        return len(self.scrobbles) == 0

    def next(self):
        return self.scrobbles[0] if self.scrobbles else None

    def pop(self):
        if self.scrobbles:
            del self.scrobbles[0]
            self.save()

    def add(self, s):
        self.scrobbles.append(s)
        self.save()


class Scrobbler(util.Listener):
    def __init__(self, session_key, enabled):
        self.cond = threading.Condition()
        self.cache = ScrobbleCache.load()
        self.session_key = session_key
        self.enabled = enabled

        self._playback_start = None
        self.running = True

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            with self.cond:
                while self.running and self.cache.is_empty():
                    self.cond.wait()

                next = self.cache.next()

            if next is not None:
                try:
                    self._scrobble(next)
                    with self.cond:
                        self.cache.pop()
                except Exception as e:
                    print(f"error scrobbling: {e}", file=sys.stderr)

    def _scrobble(self, s):
        album = s.album
        m = MULTI_DISC_RE.match(album)
        if m:
            album = m.group(1)

        info = {
            "artist": s.artist,
            "album": album,
            "track": s.title,
            "api_key": API_KEY,
            "sk": self.session_key,
        }

        if s.is_ended:
            info["timestamp"] = str(s.start_time)
            method = "track.scrobble"
        else:
            method = "track.updateNowPlaying"
        info["method"] = method

        print(f"last.fm: {method} {s.artist} / {s.title}")
        if self.enabled:
            _post(**info)

    def _enqueue(self, track, is_ended):
        s = Scrobble()
        s.artist = track.artist
        s.album = track.album
        s.title = track.title
        s.is_ended = is_ended
        s.start_time = self._playback_start
        with self.cond:
            self.cache.add(s)
            self.cond.notify_all()

    def track_playing(self, track):
        if not self._playback_start:
            self._playback_start = int(time.time())
            self._enqueue(track, False)

    def track_ended(self, track):
        self._enqueue(track, True)
        self._playback_start = None

    def shutdown(self):
        with self.cond:
            self.running = False
            self.cond.notify_all()
        self.thread.join()
        self.cache.save()


def get_scrobbler(enabled):
    session_key = util.SETTINGS.value(f"{SETTINGS_GRP}/{SETTINGS_SESSION_KEY}")
    return Scrobbler(session_key, enabled) if session_key else None


def sign(params):
    keys = list(params.keys())
    keys.sort()

    data = []
    for k in keys:
        data.append(k)
        data.append(params[k])
    data.append(SECRET)

    md5 = hashlib.md5()
    md5.update("".join(data).encode("utf-8"))
    return {"api_sig": md5.hexdigest(), **params}


def _get(**params):
    res = requests.get(API_URL, sign(params))
    _check_response(res)
    return res


def _post(**params):
    res = requests.post(API_URL, data=sign(params), timeout=5)
    _check_response(res)
    return res


def _get_xml_text(doc, tag):
    elem = doc.getElementsByTagName(tag)[0]

    text = []
    for node in elem.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text).strip()


def authorize():
    res = _get(
        method="auth.gettoken",
        api_key=API_KEY,
        format="json",
    )
    token = res.json()["token"]

    pid = os.fork()
    if pid == 0:
        user_url = f"http://www.last.fm/api/auth/?api_key={API_KEY}&token={token}"
        os.execvp("xdg-open", ["xdg-open", user_url])
        return

    input("Hit enter when the last.fm connection has been authorized...")
    res = _get(
        method="auth.getsession",
        api_key=API_KEY,
        token=token,
    )

    doc = minidom.xml.dom.minidom.parseString(res.text)
    key = _get_xml_text(doc, "key")

    util.SETTINGS.beginGroup(SETTINGS_GRP)
    util.SETTINGS.setValue(SETTINGS_SESSION_KEY, key)
    util.SETTINGS.endGroup()
    util.SETTINGS.sync()


if __name__ == "__main__":
    authorize()
