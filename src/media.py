import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class Player:
    """
    Player encapsulates playing a single file.
    """

    def __init__(self, parent, path):
        self._parent = parent
        self._path = path
        self._qmp = None

    @property
    def _player(self):
        if self._qmp is None:
            self._qmp = QMediaPlayer(self._parent)
            self._qmp.setMedia(QMediaContent(QUrl("file:" + self._path)))
            self._qmp.mediaStatusChanged.connect(self._handleStatusChange)
        return self._qmp

    def _handleStatusChange(self, status):
        if status == self.EndOfMedia:
            sys.exit(0)

    def play(self):
        self._player.play()
