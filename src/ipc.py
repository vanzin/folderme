# SPDX-License-Identifier: BSD-2-Clause
import app
import dbus
import dbus.service
import os
import osd
import pathlib
import sys
import util
import uuid
from dbus.mainloop.glib import DBusGMainLoop
from PyQt5.QtWidgets import QApplication

DBUS_SERVICE = "org.vanzin.FolderME"
DBUS_OBJECT = "/org/vanzin/FolderME"
REMOTE_CONTROL_IFACE = f"{DBUS_SERVICE}.Remote"

MP_IFACE = "org.mpris.MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
PROPS_IFACE = "org.freedesktop.DBus.Properties"


class MPRIS(dbus.service.Object, util.Listener):
    OBJECT = "/org/mpris/MediaPlayer2"
    SERVICE = "org.mpris.MediaPlayer2.folderme"

    def __init__(self, bus):
        bus_name = dbus.service.BusName(self.SERVICE, bus=bus)
        app.get().playlist.player().add_listener(self)

        self._cover_path = None
        self._cover_uri = None
        self._cover_album = None

        track = app.get().playlist.current_track()
        if track:
            self._set_cover(track.info)

        self.props = {
            MP_IFACE: {
                "CanQuit": True,
                "CanRaise": False,
                "HasTrackList": False,
                "Identity": "FolderME",
                "DesktopEntry": "org.vanzin.FolderME",
            },
            PLAYER_IFACE: {
                "CanPlay": True,
                "CanPause": True,
                "CanGoNext": True,
                "CanGoPrevious": True,
                "CanSeek": True,
                "CanControl": True,
                "Volume": 1.0,
                "Position": dbus.Int64(0),
                "Shuffle": False,
                "Rate": 1.0,
                "MinimumRate": 1.0,
                "MaximumRate": 1.0,
                "LoopStatus": "None",
                "PlaybackStatus": "Stopped",
            },
        }
        self._update_player_props(emit=False)

        dbus.service.Object.__init__(self, bus, self.OBJECT, bus_name=bus_name)

    @dbus.service.method(dbus_interface=MP_IFACE, in_signature="", out_signature="")
    def Quit(self):
        print("quit()")

    @dbus.service.method(dbus_interface=PLAYER_IFACE, in_signature="", out_signature="")
    def Next(self):
        print("next()")
        pass

    @dbus.service.method(dbus_interface=PLAYER_IFACE, in_signature="", out_signature="")
    def Previous(self):
        print("previous()")
        pass

    @dbus.service.method(dbus_interface=PLAYER_IFACE, in_signature="", out_signature="")
    def Pause(self):
        print("pause()")
        pass

    @dbus.service.method(dbus_interface=PLAYER_IFACE, in_signature="", out_signature="")
    def PlayPause(self):
        print("playpause()")
        pass

    @dbus.service.method(dbus_interface=PLAYER_IFACE, in_signature="", out_signature="")
    def Stop(self):
        print("stop()")
        pass

    @dbus.service.method(
        dbus_interface=PLAYER_IFACE, in_signature="x", out_signature=""
    )
    def Seek(self, ms):
        print("seek()")
        pass

    @dbus.service.method(
        dbus_interface=PLAYER_IFACE, in_signature="ox", out_signature=""
    )
    def SetPosition(self, track, pos):
        print("setpos()")
        pass

    @dbus.service.method(
        dbus_interface=PROPS_IFACE, in_signature="ss", out_signature="v"
    )
    def Get(self, iface, prop):
        print(f"get: {iface} {prop}")
        return self.props.get(iface, {}).get(prop)

    @dbus.service.method(
        dbus_interface=PROPS_IFACE, in_signature="ssv", out_signature=""
    )
    def Set(self, iface, prop, value):
        print(f"set: {iface}/{prop} = {value}")
        pass

    @dbus.service.method(
        dbus_interface=PROPS_IFACE, in_signature="s", out_signature="a{sv}"
    )
    def GetAll(self, iface):
        print(f"get all {iface}")
        return self.props.get(iface, {})

    @dbus.service.signal(dbus_interface=PROPS_IFACE, signature="sa{sv}as")
    def PropertiesChanged(self, iface, props, invalid):
        pass

    def track_paused(self, track):
        self._update_player_props()

    def track_playing(self, track):
        self._set_cover(track)
        self._update_player_props()

    def track_stopped(self, track):
        self._update_player_props()

    def _update_player_props(self, emit=True):
        pl = app.get().playlist

        state = "Stopped"
        if pl.is_playing():
            state = "Playing"
        elif pl.is_paused():
            state = "Paused"
        track = pl.player().track()

        meta = dbus.Dictionary({}, signature="sv")
        if track:
            meta.update(
                {
                    "mpris:trackid": f"{DBUS_OBJECT}/{track.trackno}",
                    "xesam:album": track.album,
                    "xesam:artist": track.artist,
                    "xesam:title": track.title,
                }
            )

            if self._cover_uri:
                meta["mpris:artUrl"] = self._cover_uri

        props = {
            "PlaybackStatus": state,
            "Position": dbus.Int64(0),
            "Metadata": meta,
        }

        self.props[PLAYER_IFACE].update(props)

        if emit:
            self.PropertiesChanged(PLAYER_IFACE, props, [])

    def _set_cover(self, track):
        print("in")
        album = os.path.dirname(track.path)
        if album == self._cover_album:
            return

        if self._cover_path:
            try:
                os.unlink(self._cover_path)
            except:
                pass

        art = track.cover_art()
        if art:
            self._cover_path = os.path.join(util.config_dir(), str(uuid.uuid4()))
            self._cover_uri = pathlib.Path(self._cover_path).as_uri()
            open(self._cover_path, "wb").write(art)

        self._cover_album = track.album
        print("out")


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
        self.mpris = MPRIS(bus)

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

    @dbus.service.method(
        dbus_interface=REMOTE_CONTROL_IFACE, in_signature="", out_signature=""
    )
    def osd(self):
        player = self.ui.osd.show_osd(None)


def send(cmd):
    bus = dbus.SessionBus()
    server = bus.get_object(DBUS_SERVICE, DBUS_OBJECT)
    method = getattr(server, cmd)
    method(dbus_interface=REMOTE_CONTROL_IFACE)
