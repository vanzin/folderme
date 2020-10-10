# SPDX-License-Identifier: BSD-2-Clause
import util
from PyQt5.QtWidgets import QDialog


class BrowseDialog(QDialog):
    def __init__(self, parent, collection):
        QDialog.__init__(self, parent)
        util.init_ui(self, "browser.ui")
        self.close.clicked.connect(self.hide)
