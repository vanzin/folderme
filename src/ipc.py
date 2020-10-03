# SPDX-License-Identifier: BSD-2-Clause
import dbus
import dbus.service
import os
import socket
import threading
import traceback
import sys
import util
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


def send(cmd):
    bus = dbus.SessionBus()
    server = bus.get_object(DBUS_SERVICE, DBUS_OBJECT)
    server.playpause(dbus_interface=PLAYLIST_IFACE)
