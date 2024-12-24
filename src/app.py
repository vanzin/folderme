# SPDX-License-Identifier: BSD-2-Clause
import sys

import app
import browser
import collection
import config
import ipc
import lastfm
import osd
import playlist
import randomizer
import util
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QSystemTrayIcon


_INSTANCE = None
BaseMainWindow = util.compile_ui("main.ui")
BIAS_CFG_KEY = "playlist/bias"


class TrayIcon(QSystemTrayIcon, util.Listener):
    def __init__(self, ui):
        QSystemTrayIcon.__init__(self, QIcon(util.icon("folderme.png")))
        self.ui = ui

        menu = QMenu()

        a = menu.addAction(QIcon(util.icon("play.png")), "Play")
        a.triggered.connect(app.get().playlist.playpause)

        a = menu.addAction(QIcon(util.icon("pause.png")), "Pause")
        a.triggered.connect(app.get().playlist.playpause)

        a = menu.addAction(QIcon(util.icon("stop.png")), "Stop")
        a.triggered.connect(app.get().playlist.playpause)

        a = menu.addAction(QIcon(util.icon("quit.png")), "Quit")
        a.triggered.connect(self.ui.handleQuit)

        self.setContextMenu(menu)

        self.activated.connect(self._activated)
        self.setToolTip("Stopped")
        util.EventBus.add(self)

    def _activated(self, reason):
        if reason != QSystemTrayIcon.Trigger:
            return

        if self.ui.isVisible():
            self.ui.hide()
        else:
            self.ui.show()
            QTimer.singleShot(0, self._do_raise)

    def track_playing(self, track):
        self.setToolTip(f"Playing: {track.artist} - {track.title}")

    def track_paused(self, track):
        self.setToolTip(f"Paused: {track.artist} - {track.title}")

    def track_stopped(self, track):
        self.setToolTip(f"Stopped")

    def _do_raise(self):
        self.ui.activateWindow()
        self.ui.raise_()


class MainWindow(BaseMainWindow, util.Listener):
    def __init__(self, args):
        BaseMainWindow.__init__(self)

        c = app.get().collection
        util.EventBus.add(self)

        p = app.get().playlist
        p.init_ui(self)

        self.driver = randomizer.Randomizer.load()

        self.playPause.clicked.connect(self.handlePlayPause)
        self.next.clicked.connect(p.next)
        self.previous.clicked.connect(p.prev)
        self.stop.clicked.connect(p.stop)

        self.nextAlbum.clicked.connect(lambda x: self.driver.pick_next())
        self.browser.clicked.connect(lambda x: self.show_browser())
        self.rescan.clicked.connect(lambda x: self.do_rescan())
        self.config.clicked.connect(lambda x: self.show_config())
        self.quit.clicked.connect(lambda x: self.handleQuit())

        self.playlistUI.setFocus()
        util.restore_ui(self, "main")

    def handlePlayPause(self):
        if not app.get().playlist.albums:
            self.driver.pick_next()
        app.get().playlist.playpause()

    def handleQuit(self):
        util.EventBus.send(util.Listener.ui_exit)
        self.driver.save()
        util.save_ui(self, "main")
        app.get().exit()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        util.EventBus.send(util.Listener.ui_resized, self)

    def showEvent(self, e):
        super().showEvent(e)
        util.EventBus.send(util.Listener.ui_resized, self)

    def closeEvent(self, e):
        self.driver.save()
        util.save_ui(self, "main")
        super().closeEvent(e)

    def show_browser(self):
        browser.BrowseDialog(self).show()

    def show_config(self):
        cfg = config.ConfigDialog()
        cfg.exec()

    def collection_changed(self):
        self.repaint()

    def do_rescan(self):
        app.get().collection.scan(self)


class FolderME(QApplication):
    def __init__(self):
        QApplication.__init__(self, sys.argv)
        self.setWindowIcon(QIcon(util.icon("folderme.png")))

    def init(self, args):
        self._pixmaps = util.PixmapCache()
        self._collection = collection.Collection.load()
        self._playlist = playlist.Playlist.load()
        self._scrobbler = lastfm.get_scrobbler(not args.no_lastfm)
        if self._scrobbler:
            util.EventBus.add(self._scrobbler)

        self._bias = 1

        bias = util.SETTINGS.value(BIAS_CFG_KEY)
        if bias:
            self._bias = int(bias)

    @property
    def pixmaps(self):
        return self._pixmaps

    @property
    def collection(self):
        return self._collection

    @property
    def playlist(self):
        return self._playlist

    @property
    def bias(self):
        return self._bias

    def set_bias(self, bias):
        self._bias = bias
        util.SETTINGS.setValue(BIAS_CFG_KEY, str(bias))

    def save(self):
        self.playlist.save()

    def exit(self):
        self.save()
        if self._scrobbler:
            self._scrobbler.shutdown()
        self.quit()


def init(args):
    global _INSTANCE

    if args.no_save:
        util.ConfigObj.SAVE_ENABLED = False

    _INSTANCE = FolderME()
    _INSTANCE.init(args)


def start(args):
    init(args)

    if not get().collection.albums:
        cfg = config.ConfigDialog()
        cfg.exec()

    if get().collection.needs_rescan():
        get().collection.scan()

    mainUI = MainWindow(args)
    osd.init()

    if not args.no_dbus:
        server = ipc.Server(mainUI)

    tray = TrayIcon(mainUI)
    tray.show()

    if args.show:
        mainUI.show()

    sys.exit(get().exec_())


def get():
    return _INSTANCE
