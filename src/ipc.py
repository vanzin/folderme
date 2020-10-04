# SPDX-License-Identifier: BSD-2-Clause
import dbus
import dbus.service
import sys
from dbus.mainloop.glib import DBusGMainLoop
from PyQt5.QtWidgets import QApplication

DBUS_SERVICE = "org.vanzin.FolderME"
DBUS_OBJECT = "/org/vanzin/FolderME"
REMOTE_CONTROL_IFACE = f"{DBUS_SERVICE}.Remote"


class Server(dbus.service.Object):
    def __init__(self, ui):
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()

        claimed = False
        try:
            bus.get_name_owner(DBUS_SERVICE)
            claimed = True
        except:
            pass

        if claimed:
            raise Exception("DBUS service already claimed.")

        bus_name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
        dbus.service.Object.__init__(self, bus, DBUS_OBJECT, bus_name=bus_name)
        self.ui = ui

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def playpause(self):
        if not self.ui.playlist.albums and not self.ui.playlist.is_playing():
            self.ui.driver.pick_next(play=True)
        else:
            self.ui.playlist.playpause()

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def stop(self):
        self.ui.playlist.stop()

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def quit(self):
        self.ui.handleQuit()

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def next(self):
        self.ui.playlist.next()

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def prev(self):
        self.ui.playlist.prev()

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def stop_after_track(self):
        self.ui.playlist.stop_after(self.ui.playlist.current_track())


def send(cmd):
    bus = dbus.SessionBus()
    server = bus.get_object(DBUS_SERVICE, DBUS_OBJECT)
    method = getattr(server, cmd)
    method(dbus_interface=REMOTE_CONTROL_IFACE)
