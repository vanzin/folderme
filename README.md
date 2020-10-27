folderme - a folder-based music player
======================================

FolderME is a music player that understands collections organized by folders. It treats
one folder as one album, regardless of what's actually in the folder.

It is not for everybody; in fact it's been written to do exactly what I expect from a
music player:

* play albums in random order (not shuffle!), one at a time
* allow stopping playback after current song
* allow skipping individual songs
* allow manually appending and removing albums from the playlist

Bonus:

* Last.fm integration
* MPRIS2 (D-Bus) support


Running
-------

* requires a few python libraries (see DEBIAN/control)
* just run `src/folderme`

Or build a Debian package and install it to get better D-Bus / desktop integration.
