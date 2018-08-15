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
Leopold Mozart: Violinschule, Editing Panel
"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import panel
import actioncollection
import actioncollectionmanager
import icons

class MozartPanel(panel.Panel):
    def __init__(self, mainwindow):
        super(MozartPanel, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+Z"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        ac = self.actionCollection = Actions(self)

    def translateUI(self):
        self.setWindowTitle(_("Leopold Mozart: Violinschule"))
        self.toggleViewAction().setText(_("&Mozart"))

    def createWidget(self):
        from . import widget
        w = widget.Widget(self)
        return w

class Actions(actioncollection.ActionCollection):
    name = "mozart"

    def createActions(self, parent=None):
        # Navigational actions
        self.mozart_previous_example = QAction(parent)
        self.mozart_previous_example.setIcon(icons.get('go-previous'))
        self.mozart_next_example = QAction(parent)
        self.mozart_next_example.setIcon(icons.get('go-next'))

        # Show examples actions
        self.mozart_open_file = QAction(parent)
        self.mozart_open_file_exclusive = QAction(parent)
        self.mozart_close_file = QAction(parent)
        self.mozart_show_manuscript = QAction(parent)

        # Create files actions
        self.mozart_create_one_voice = QAction(parent)
        self.mozart_create_one_system = QAction(parent)
        self.mozart_create_two_systems = QAction(parent)
        self.mozart_create_include = QAction(parent)
        self.mozart_create_one_voice_2 = QAction(parent)
        self.mozart_create_one_system_2 = QAction(parent)
        self.mozart_create_two_systems_2 = QAction(parent)

        # Process examples actions
        self.mozart_process_example = QAction(parent)
        self.mozart_process_example.setIcon(icons.get('lilypond-run'))
        self.mozart_process_visible_examples = QAction(parent)
        self.mozart_process_visible_examples.setIcon(icons.get('lilypond-run'))
        self.mozart_process_examples = QAction(parent)
        self.mozart_process_examples.setIcon(icons.get('lilypond-run'))
        self.mozart_process_pause = QAction(parent)
        self.mozart_process_pause.setIcon(icons.get('media-playback-pause'))
        self.mozart_process_resume = QAction(parent)
        self.mozart_process_resume.setIcon(icons.get('media-playback-start'))
        self.mozart_process_abort = QAction(parent)
        self.mozart_process_abort.setIcon(icons.get('media-playback-stop'))


    def translateUI(self):
        self.mozart_previous_example.setText("&Voriges Beispiel")
        self.mozart_next_example.setText("&Nächstes Beispiel")
        self.mozart_open_file.setText("Öffne in &Editor")
        self.mozart_open_file_exclusive.setText("Öffne in Editor (e&xklusiv)")
        self.mozart_close_file.setText("&Schließe im Editor")
        self.mozart_show_manuscript.setText("Zeige &Manuskript")

        self.mozart_create_one_voice.setText("Datei (eine S&timme)")
        self.mozart_create_one_system.setText("&Datei (ein System)")
        self.mozart_create_two_systems.setText("Datei (&zwei Systeme)")
        self.mozart_create_include.setText("&Include-Datei")
        self.mozart_create_one_voice_2.setText("Beide Dateien (eine Sti&mme)")
        self.mozart_create_one_system_2.setText("&Beide Dateien (ein System)")
        self.mozart_create_two_systems_2.setText(
            "Beide Dateien (zwei &Systeme)")

        self.mozart_process_example.setText("Erzeuge aktuelles Beispiel")
        self.mozart_process_visible_examples.setText(
            "Erzeuge sichtbare Beispiele")
        self.mozart_process_examples.setText("Erzeuge alle Beispiele")

        self.mozart_process_pause.setText("Unterbreche Prozess (aktuelle Jobs werden noch beendet)")
        self.mozart_process_resume.setText("Setze unterbrochenen Prozess fort")
        self.mozart_process_abort.setText("Breche Prozess ab")

    def update_actions(self):
        data = self.widget().widget().examples_widget.example_data()
        self.mozart_open_file.setEnabled(data['file'] or data['include'])
        self.mozart_open_file_exclusive.setEnabled(
            self.mozart_open_file.isEnabled())
        self.mozart_close_file.setEnabled(self.mozart_open_file.isEnabled())

        self.mozart_create_one_voice.setEnabled(not data['file'])
        self.mozart_create_one_system.setEnabled(
            self.mozart_create_one_voice.isEnabled())
        self.mozart_create_two_systems.setEnabled(
            self.mozart_create_one_voice.isEnabled())
        self.mozart_create_include.setEnabled(
            data['file'] and not data['include'])
        self.mozart_create_one_voice_2.setEnabled(
            self.mozart_create_one_voice.isEnabled())
        self.mozart_create_one_system_2.setEnabled(
            self.mozart_create_one_voice.isEnabled())
        self.mozart_create_two_systems_2.setEnabled(
            self.mozart_create_one_voice.isEnabled())

        self.mozart_process_example.setEnabled(data['file'])
