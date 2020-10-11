# SPDX-License-Identifier: BSD-2-Clause
import app
import playlist
import random
import time
import util


class Randomizer(util.Listener):
    def __init__(self):
        self.rnd = random.Random(time.time())
        app.get().playlist.add_listener(self)

    def playlist_ended(self):
        self.pick_next(play=True)

    def pick_next(self, play=False):
        if not self.collection.albums:
            print("No albums.")
            return

        ignore = [x.artist for x in app.get().playlist.albums]
        while True:
            next = self.rnd.choice(app.get().collection.albums)
            if next.artist in ignore:
                continue

            print(f"Playing {next.artist}/{next.title}")
            app.get().playlist.replace(next, play=play)
            return
