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
Leopold Mozart Violinschule Kontrollcenter
"""


from PyQt5.QtWidgets import (
    QTabWidget,
    QWidget
)

from . import (
    config,
    examples
)

class Widget(QTabWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool)
        self.config_widget = cw = config.ConfigWidget(self)
        self.examples_widget = examples.ExamplesWidget(cw)
        self.addTab(self.examples_widget, "Beispiele")
        self.addTab(self.config_widget, "Konfiguration")
