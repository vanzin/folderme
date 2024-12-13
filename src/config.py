# SPDX-License-Identifier: BSD-2-Clause
import app
import util
from PySide6.QtWidgets import QFileDialog


class ConfigDialog(util.compile_ui("config.ui")):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lSources.clear()
        for path in app.get().collection.locations:
            self.lSources.addItem(path)

        self.sbBias.setValue(app.get().bias)
        self.accepted.connect(self._ok)
        self.rejected.connect(self._cancel)

        self.bAdd.clicked.connect(self._add_source)
        self.bRemove.clicked.connect(self._remove_source)

    def _add_source(self):
        path = QFileDialog.getExistingDirectory(self)
        if path:
            self.lSources.addItem(path)

    def _remove_source(self):
        for i in self.lSources.selectedItems():
            r = self.lSources.takeItem(self.lSources.row(i))

    def _ok(self):
        sources = [self.lSources.item(x).text() for x in range(self.lSources.count())]
        app.get().collection.locations = sources
        app.get().collection.scan(self)

        app.get().collection.save()
        app.get().set_bias(self.sbBias.value())
        app.get().save()

    def _cancel(self):
        self.close()
