# SPDX-License-Identifier: BSD-2-Clause
import random
import time

import app
import util


class Randomizer(util.ConfigObj, util.Listener):
    def __init__(self):
        self.history = []
        self._rnd = random.Random(time.time())
        self._now_playing = None
        util.EventBus.add(self)

    def track_playing(self, track):
        new_artist = track.artist
        if self._now_playing and new_artist != self._now_playing:
            self._add_to_history(self._now_playing)

        self._now_playing = new_artist

    def playlist_ended(self):
        if self._now_playing:
            self._add_to_history(self._now_playing)
            self._now_playing = None

        self.pick_next(play=True)

    def pick_next(self, play=False):
        if not app.get().collection.albums:
            print("No albums.")
            return

        ignore = self.history + [x.info.artist for x in app.get().playlist.albums]
        while True:
            next = self._rnd.choice(app.get().collection.albums)
            if next.artist in ignore:
                continue

            app.get().playlist.replace(next, play=play)
            return

    def _add_to_history(self, artist):
        self.history.append(artist)
        if len(self.history) > app.get().bias:
            del self.history[0]
        self.save()
