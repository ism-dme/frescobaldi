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
Produce a number of examples for final use.
"""

from PyQt5.QtCore import (
    QSettings,
    Qt,
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListView,
    QSizePolicy,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget
)

import widgets.dialog

def create_examples(examples, widget):
    """Take a list of example names and produce all the relevant
    output files. 'widget' is the QTabWidget holding the
    example_widget and config_widget tabs. 'examples' is a string list."""
    dlg = ProcessDialog(examples, widget, parent=widget.mainwindow())
    dlg.exec_()


class ProcessDialog(widgets.dialog.Dialog):

    def __init__(self, examples, widget, parent=None):
        super(ProcessDialog, self).__init__(
            buttons=('ok',),
            title="Erzeuge Beispiel(e)",
            #message="Hey, das ist die Message"
            )

        self.examples = examples
        ac = widget.action_collection

        layout = QGridLayout()
        self.mainWidget().setLayout(layout)

        self.toolbar = QToolBar(self)
        self.toolbar.addAction(ac.mozart_process_abort)
        self.toolbar.addAction(ac.mozart_process_pause)
        self.toolbar.addAction(ac.mozart_process_resume)
        ac.mozart_process_resume.setEnabled(False)

        self.activities_view = ActivitiesView(self)
        self.results_view = ResultsView(examples, self)

        layout.addWidget(self.toolbar, 0, 0, 1, 2)
        layout.addWidget(self.activities_view, 1, 0, 1, 1)
        layout.addWidget(self.results_view, 1, 1, 1, 1)

class ActivitiesView(QTableView):

    def __init__(self, parent=None):
        super(ActivitiesView, self).__init__(parent)
        num_runners = QSettings().value('mozart/num-runners', 1, int)
        self.setModel(QStandardItemModel())
        self.setFixedWidth(230)
        self.model().setHorizontalHeaderLabels(
        ['Beispiel', 'Typ'])
        self.initialize(num_runners)
        self.model().setVerticalHeaderLabels(
            [str(i + 1) for i in range(num_runners)]
        )
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


    def initialize(self, num_runners):
        root = self.model().invisibleRootItem()
        for i in range(num_runners):
            root.appendRow([QStandardItem('--'), QStandardItem('--')])

    def stop_runner(self, runner):
        self.update_runner(runner, '--', '--')

    def update_runner(self, runner, example, type):
        parent = self.model().invisibleRootItem()
        parent.child(runner, 0).setText(example)
        parent.child(runner, 1).setText(type)

class ResultsView(QTableView):

    def __init__(self, examples, parent=None):
        super(ResultsView, self).__init__(parent)
        self.examples = examples
        self.setModel(QStandardItemModel())
        self.model().setHorizontalHeaderLabels(
            ['PDF', 'PNG', 'SVG'])
        for col in range(3):
            self.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents)

        root = self.model().invisibleRootItem()
        for example in examples:
            pdf_item = QStandardItem()
            pdf_item.setCheckable(False)
            pdf_item.setCheckState(Qt.Unchecked)
            png_item = QStandardItem(True)
            png_item.setCheckable(False)
            png_item.setCheckState(Qt.Unchecked)
            svg_item = QStandardItem()
            svg_item.setCheckable(False)
            svg_item.setCheckState(Qt.Unchecked)
            root.appendRow([pdf_item, png_item, svg_item])
        self.model().setVerticalHeaderLabels(examples)
