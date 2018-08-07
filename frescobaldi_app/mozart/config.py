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


from PyQt5.QtCore import (
    QSettings
)
from PyQt5.QtGui import (
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget
)

from widgets import urlrequester


class ConfigWidget(QWidget):
    def __init__(self):
        super(ConfigWidget, self).__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        url_layout = QHBoxLayout()
        self.url_label = QLabel(self)
        self.url_label.setText("Projekt-Root:")
        self.urlrequester = urlrequester.UrlRequester(self)
        self.urlrequester.changed.connect(self.save_root)
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.urlrequester)
        layout.addLayout(url_layout)


        layout.addStretch()

        self.load_settings()

    def load_settings(self):
        s = QSettings()
        s.beginGroup('mozart')
        self.urlrequester.setPath(s.value('root', ''))

    def project_root(self):
        return self.urlrequester.path()
        
    def save_root(self):
        s = QSettings()
        s.setValue('mozart/root', self.urlrequester.path())
