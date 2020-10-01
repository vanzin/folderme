# SPDX-License-Identifier: BSD-2-Clause
import collection
import util

if __name__ == "__main__":
    c = util.load_config(collection.Collection)

    if not c.albums:
        print("Scanning")
        c.scan()

    for a in c.albums:
        print(str(a))

    util.save_config(c)
