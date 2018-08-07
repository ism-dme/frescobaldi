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
Leopold Mozart Violinschule Beispiel-Übersicht
"""

import re
import os

from PyQt5.QtCore import (
    QSettings,
    Qt
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QTreeView,
    QVBoxLayout,
    QWidget
)


class ExamplesWidget(QWidget):
    def __init__(self, config):
        super(ExamplesWidget, self).__init__()
        self._config = config
        config_layout = QHBoxLayout()
        layout = QVBoxLayout()
        layout.addLayout(config_layout)
        self.setLayout(layout)

        # TODO: Fill config_layout with widgets

        # Configure TreeView
        self.tree_view = tv = QTreeView(self)
        tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.model = ExamplesModel(config, self)
        tv.setModel(self.model)
        tv.model().populate()

        layout.addWidget(tv)


    def config(self):
        return self._config

    def save_settings(self):
        s = QSettings()
        s.beginGroup('mozart')
        s.setValue('example-columns/name', self.tree_view.columnWidth(0))


class ExamplesModel(QStandardItemModel):
    """Model for info about examples"""
    def __init__(self, config, parent=None):
        super(ExamplesModel, self).__init__(parent)
        self.config = config
        self.project_root = self.config.project_root()
        self.source = os.path.join(self.project_root,
            'vorlage', 'beispiel-liste')

        self.itemChanged.connect(self.slot_item_changed)

    def load_column_widths(self):
        """Load the column widths from settings."""
        #TODO: This doesn't work yet because ExamplesWidget.save_settings is
        # never called!
        s = QSettings()
        s.beginGroup('mozart')
        self.parent().tree_view.setColumnWidth(0,
            s.value('example-columns/name', 250))
        self.parent().tree_view.setColumnWidth(1, 25)
        self.parent().tree_view.setColumnWidth(2, 25)
        self.parent().tree_view.setColumnWidth(3, 60)
        self.parent().tree_view.setColumnWidth(4, 60)
        self.parent().tree_view.setColumnWidth(5, 60)

    def populate(self):
        """(Re-)Populate the model based on parsing
        <project_root>/vorlage/beispiel-liste."""
        re_heading = re.compile('(\**) (.*)')
        self.clear()
        self.setHorizontalHeaderLabels([
            'Beispiel',
            'File',
            'Inc.',
            'Eingabe',
            'Review',
            'Abgenommen'
        ])
        self.load_column_widths()

        with open(self.source) as f:
            input = f.read().split('\n')
        root = self.invisibleRootItem()

        last_toplevel = None
        last_secondlevel = None
        for line in input:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re_heading.match(line)
            if match:
                # Handle top/second-level headings
                level, title = match.groups()
                if level == '*':
                    last_toplevel = QStandardItem(title)
                    last_secondlevel = None
                    root.appendRow(last_toplevel)
                else:
                    last_secondlevel = QStandardItem(title)
                    last_toplevel.appendRow(last_secondlevel)
            else:
                # Handle single example
                parent = last_secondlevel or last_toplevel

                xmp_info = line.split(' ')
                xmp_name = xmp_info[0]
                row = [QStandardItem(xmp_name)]

                # Check if the main example .ly file is present (mandatory)
                has_file_item = QStandardItem()
                has_file_item.setCheckable(False)
                xmp_file = os.path.join(self.project_root,
                    "{}.ly".format(xmp_name))
                has_file = Qt.Checked if os.path.isfile(xmp_file) else Qt.Unchecked
                has_file_item.setCheckState(has_file)
                row.append(has_file_item)

                # Check if an <example>-include.ily file is present
                has_include_item = QStandardItem()
                has_include_item.setCheckable(False)
                include_file = os.path.join(
                    self.project_root, "{}-include.ily".format(xmp_name))
                has_include = Qt.Checked if os.path.isfile(include_file) else Qt.Unchecked
                has_include_item.setCheckState(has_include)
                row.append(has_include_item)

                # Check if example has been marked as input
                has_input_item = QStandardItem()
                has_input_item.setCheckable(True)
                has_input = Qt.Checked if xmp_info[1] == '[x]' else Qt.Unchecked
                has_input_item.setCheckState(has_input)
                row.append(has_input_item)

                # Check if example has been marked as ready for review
                for_review_item = QStandardItem()
                for_review_item.setCheckable(True)
                for_review = Qt.Checked if xmp_info[2] == '[x]' else Qt.Unchecked
                for_review_item.setCheckState(for_review)
                row.append(for_review_item)

                # Check if example has been approved
                approved_item = QStandardItem()
                approved_item.setCheckable(True)
                approved = Qt.Checked if xmp_info[3] == '[x]' else Qt.Unchecked
                approved_item.setCheckState(approved)
                row.append(approved_item)

                parent.appendRow(row)

    def slot_item_changed(self, item):
        index = self.indexFromItem(item)
        example = index.sibling(index.row(), 0)
        example_name = self.itemFromIndex(example).text()
        col = item.column()
        new_state = True if item.checkState() == 2 else False

        if col < 3:
            return

        # Update the source file
        with open(self.source) as f:
            input = f.read().split('\n')
        output = []
        for line in input:
            if not line.startswith(example_name):
                output.append(line)
            else:
                xmp_info = line.split(' ')
                xmp_info[col - 2] = '[x]' if new_state else '[]'
                output.append(' '.join(xmp_info))

        with open(self.source, 'w') as f:
            f.write('\n'.join(output))
