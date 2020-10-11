# SPDX-License-Identifier: BSD-2-Clause
import app
import browser
import util
from PyQt5.QtWidgets import QDialog, QFileDialog


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        util.init_ui(self, "config.ui")

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

        dlg = browser.ScanDialog(self)
        app.get().collection.scan(dlg)
        dlg.exec()

        app.get().collection.save()
        app.get().set_bias(self.sbBias.value())
        app.get().save()

    def _cancel(self):
        self.close()

    def scan_done(self):
        pass
