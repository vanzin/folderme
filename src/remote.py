# SPDX-License-Identifier: BSD-2-Clause
import dbus
import dbus.service

DBUS_SERVICE = "org.vanzin.FolderME"
DBUS_OBJECT = "/org/vanzin/FolderME"
REMOTE_CONTROL_IFACE = f"{DBUS_SERVICE}.Remote"


def send(cmd):
    bus = dbus.SessionBus()
    server = bus.get_object(DBUS_SERVICE, DBUS_OBJECT)
    method = getattr(server, cmd)
    method(dbus_interface=REMOTE_CONTROL_IFACE)
