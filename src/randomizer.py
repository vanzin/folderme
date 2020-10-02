# SPDX-License-Identifier: BSD-2-Clause
import playlist
import random
import time


class Randomizer(playlist.Listener):
    def __init__(self, collection, plist):
        self.collection = collection
        self.rnd = random.Random(time.time())
        self.playlist = plist
        plist.add_listener(self)

    def playlist_ended(self, plist):
        self.pick_next(play=True)

    def pick_next(self, play=False):
        if not self.collection.albums:
            print("No albums.")
            return

        ignore = [x.artist for x in self.playlist.albums]
        while True:
            next = self.rnd.choice(self.collection.albums)
            if next.artist in ignore:
                continue

            print(f"Playing {next.artist}/{next.title}")
            self.playlist.replace(next, play=play)
            return
