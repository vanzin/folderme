# SPDX-License-Identifier: BSD-2-Clause
import playlist


class Randomizer(playlist.Listener):
    def __init__(self, collection, plist):
        self.collection = collection
        plist.add_listener(self)

    def playlist_ended(self, plist):
        plist.replace(self.collection.albums[0])
