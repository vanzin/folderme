# SPDX-License-Identifier: BSD-2-Clause
import argparse
import dbus
import dbus.service
import sys
from dbus.mainloop.glib import DBusGMainLoop
from PyQt5.QtWidgets import QApplication

DBUS_SERVICE = "org.vanzin.FolderME"
DBUS_OBJECT = "/org/vanzin/FolderME"
PLAYLIST_IFACE = f"{DBUS_SERVICE}.Playlist"


class Server(dbus.service.Object):
    def __init__(self, ui):
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
        dbus.service.Object.__init__(self, bus_name, DBUS_OBJECT)
        self.ui = ui

    @dbus.service.method(
        dbus_interface=PLAYLIST_IFACE, in_signature="", out_signature=""
    )
    def playpause(self):
        if not self.ui.playlist.albums and not self.ui.playlist.is_playing():
            self.ui.driver.pick_next(play=True)
        else:
            self.ui.playlist.playpause()

    @dbus.service.method(
        dbus_interface=PLAYLIST_IFACE, in_signature="", out_signature=""
    )
    def stop(self):
        self.ui.playlist.stop()

    @dbus.service.method(
        dbus_interface=PLAYLIST_IFACE, in_signature="", out_signature=""
    )
    def quit(self):
        self.ui.handleQuit()

    @dbus.service.method(
        dbus_interface=PLAYLIST_IFACE, in_signature="", out_signature=""
    )
    def next(self):
        self.ui.playlist.next()

    @dbus.service.method(
        dbus_interface=PLAYLIST_IFACE, in_signature="", out_signature=""
    )
    def prev(self):
        self.ui.playlist.prev()


def main(argv):
    parser = argparse.ArgumentParser(description="FolderME remote control")
    parser.add_argument("--remote", metavar="CMD", help="command to send to FolderME")
    args = parser.parse_args(argv[1:])

    bus = dbus.SessionBus()
    server = bus.get_object(DBUS_SERVICE, DBUS_OBJECT)
    method = getattr(server, args.remote)
    method(dbus_interface=PLAYLIST_IFACE)
    return 0
