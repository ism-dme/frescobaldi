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
Leopold Mozart: Violinschule. Kontextmenü(s).
"""

from PyQt5.QtWidgets import QMenu, QAction

class ContextMenu(QMenu):
    """Kontextmenü für den Beispiel-Baum.
    Aktionen beinhalten die Anzeige im Editor, das Erzeugen neuer Dateien
    und das Anzeigen des Manuskripts."""
    def __init__(self, parent):
        super(ContextMenu, self).__init__(parent)

        ac = self.action_collection = parent.action_collection
        self.addAction(ac.mozart_previous_example)
        self.addAction(ac.mozart_next_example)
        self.addSeparator()

        self.addAction(ac.mozart_open_file)
        self.addAction(ac.mozart_open_file_exclusive)
        self.addAction(ac.mozart_close_file)
        self.addSeparator()

        self.addMenu(self.new_files_menu())
        self.addSeparator()

        self.addAction(ac.mozart_show_manuscript)
        ac.update_actions()

    def new_files_menu(self):
        m = QMenu("&Neu", self)
        ac = self.action_collection
        m.addAction(ac.mozart_create_one_voice)
        m.addAction(ac.mozart_create_one_system)
        m.addAction(ac.mozart_create_two_systems)
        m.addAction(ac.mozart_create_include)
        m.addSeparator()

        m.addAction(ac.mozart_create_one_voice_2)
        m.addAction(ac.mozart_create_one_system_2)
        m.addAction(ac.mozart_create_two_systems_2)
        return m
