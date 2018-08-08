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
    def __init__(self, position, data, parent=None):
        super(ContextMenu, self).__init__(parent)
        self.position = position
        self.data = data

        self.open_file = of = QAction(self)
        of.setText("Öffne in &Editor")
        self.addAction(of)

        self.close_file = clf = QAction(self)
        clf.setText("&Schließe im Editor")
        self.addAction(clf)

        self.addSeparator()

        self.create_file = cf = QAction(self)
        cf.setText("&Neue Datei (ein System)")
        self.addAction(cf)

        self.create_file_2 = cf2 = QAction(self)
        cf2.setText("&Neue Datei (zwei Systeme)")
        self.addAction(cf2)

        self.create_include = ci = QAction(self)
        ci.setText("Neue &Include-Datei")
        self.addAction(ci)

        self.addSeparator()

        self.create_files = cfs = QAction(self)
        cfs.setText("Neue &Dateien (ein System)")
        self.addAction(cfs)

        self.create_files_2 = cfs2 = QAction(self)
        cfs2.setText("Neue Dateien (zwei &Systeme)")
        self.addAction(cfs2)        

        self.show_manuscript = sm = QAction(self)
        sm.setText("Zeige &Manuskript")
        self.addAction(sm)

        self.update_actions()

    def update_actions(self):
        self.open_file.setEnabled(self.data['file'] or self.data['include'])
        self.close_file.setEnabled(self.open_file.isEnabled())
        self.create_file.setEnabled(not self.data['file'])
        self.create_file_2.setEnabled(self.create_file.isEnabled())
        self.create_include.setEnabled(
            self.data['file'] and not self.data['include'])
        self.create_files.setEnabled(
            not self.data['file']
            and not self.data['include'])


def show(tree_view, position, data):
    """Shows a context menu.

    data: a dictionary with keys
    - example
    - file
    - include
    - input
    - preview
    - approved
    """
    m = QMenu(tree_view)
    open_file = QAction(tree_view)
    open_file.setText("Öffne in &Editor")
    open_file.setEnabled(data['file'] or data['include'])
    m.addAction(open_file)

    create_file = QAction(tree_view)
    create_file.setText("&Neue Datei")
    create_file.setEnabled(not data['file'])
    m.addAction(create_file)

    create_include = QAction(tree_view)
    create_include.setText("Neue &Include-Datei")
    create_include.setEnabled(data['file'] and not data['include'])
    m.addAction(create_include)

    show_manuscript = QAction(tree_view)
    show_manuscript.setText("Zeige &Manuskript")
    m.addAction(show_manuscript)

    # Update actions


    # show it!
    if m.actions():
        m.exec_(tree_view.mapToGlobal(position))
    m.deleteLater()
