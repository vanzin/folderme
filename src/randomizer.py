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
        self._now_playing = track.artist

    def playlist_ended(self):
        if self._now_playing:
            self.history.append(self._now_playing)
            self._now_playing = None
            if len(self.history) > app.get().bias:
                del self.history[0]

        self.pick_next(play=True)
        self.save()

    def pick_next(self, play=False):
        if not app.get().collection.albums:
            print("No albums.")
            return

        ignore = self.history + [x.info.artist for x in app.get().playlist.albums]
        while True:
            next = self._rnd.choice(app.get().collection.albums)
            if next.artist in ignore:
                continue

            print(f"Playing {next.artist}/{next.title}")
            app.get().playlist.replace(next, play=play)
            return
