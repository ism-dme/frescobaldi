# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Leopold Mozart Violinschule Konfiguration
"""

import os

from PyQt5.QtCore import (
    QSettings,
    QThread
)
from PyQt5.QtGui import (
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget
)

from widgets import urlrequester


class ConfigWidget(QWidget):
    def __init__(self, parent=None):
        super(ConfigWidget, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        root_layout = QHBoxLayout()
        self.root_label = QLabel(self)
        self.root_label.setText("Projekt-Root:")
        self.root_requester = urlrequester.UrlRequester(self)
        self.root_requester.changed.connect(self.save_root)
        root_layout.addWidget(self.root_label)
        root_layout.addWidget(self.root_requester)
        layout.addLayout(root_layout)

        export_layout = QHBoxLayout()
        self.export_label = QLabel(self)
        self.export_label.setText("Export-Verzeichnis:")
        self.export_requester = urlrequester.UrlRequester(self)
        self.export_requester.changed.connect(self.save_export)
        export_layout.addWidget(self.export_label)
        export_layout.addWidget(self.export_requester)
        layout.addLayout(export_layout)

        runner_layout = QHBoxLayout()
        self.runner_label = QLabel("Anzahl paralleler Jobs")
        self.runner_spinbox = QSpinBox()
        self.runner_spinbox.setRange(1, QThread.idealThreadCount())
        self.runner_spinbox.valueChanged.connect(self.save_runners)
        runner_layout.addWidget(self.runner_label)
        runner_layout.addWidget(self.runner_spinbox)
        layout.addLayout(runner_layout)

        layout.addStretch()

        self.load_settings()

    def load_settings(self):
        s = QSettings()
        s.beginGroup('mozart')
        self.root_requester.setPath(s.value('root', ''))
        self.export_requester.setPath(s.value('export',
            os.path.join(self.root_requester.path(), 'export')))
        self.runner_spinbox.setValue(s.value('num-runners', 1, int))

    def project_root(self):
        return self.root_requester.path()

    def save_export(self):
        QSettings().setValue('mozart/export', self.export_requester.path())

    def save_root(self):
        s = QSettings()
        s.setValue('mozart/root', self.root_requester.path())

    def save_runners(self, new_value):
        QSettings().setValue('mozart/num-runners', new_value)
