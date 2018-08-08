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
    Qt,
    QUrl
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

import app
import panelmanager
from . import contextmenu

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

        tv.setContextMenuPolicy(Qt.CustomContextMenu)
        tv.customContextMenuRequested.connect(self.show_context_menu)


    def config(self):
        return self._config

    def mainwindow(self):
        return self.config().parent().parent().parent().mainwindow()

    def save_settings(self):
        s = QSettings()
        s.beginGroup('mozart')
        s.setValue('example-columns/name', self.tree_view.columnWidth(0))

    def example_data(self, point):
        """Ermittle den Datensatz unter dem Mauszeiger."""
        model = self.tree_view.model()
        index = self.tree_view.indexAt(point)
        row = index.row()
        col = index.column()
        parent = model.itemFromIndex(index.parent())
        if not parent:
            return None
        xmp_name = parent.child(row).text()
        if not xmp_name.startswith('1756'):
            return None
        return {
            'example': xmp_name,
            'column': col,
            'file': parent.child(row, 1).checkState() == Qt.Checked,
            'include': parent.child(row, 2).checkState() == Qt.Checked,
            'input': parent.child(row, 3).checkState() == Qt.Checked,
            'review': parent.child(row, 4).checkState() == Qt.Checked,
            'approved': parent.child(row, 5).checkState() == Qt.Checked,
        }

    def show_context_menu(self, point):
        self.selected_example_data = example_data = self.example_data(point)
        if example_data:
            #contextmenu.show(self.tree_view, point, example_data)
            cm = contextmenu.ContextMenu(point, example_data, self.tree_view)
            cm.open_file.triggered.connect(self.open_file)
            cm.close_file.triggered.connect(self.close_file)
            cm.create_file.triggered.connect(self.create_file)
            cm.create_file_2.triggered.connect(self.create_file_2)
            cm.create_files.triggered.connect(self.create_files)
            cm.create_files_2.triggered.connect(self.create_files_2)
            cm.create_include.triggered.connect(self.create_include)
            cm.show_manuscript.triggered.connect(self.show_manuscript)
            cm.exec_(self.tree_view.mapToGlobal(point))
            cm.deleteLater()

    def close_file(self):
        """Schließt die Datei(en) des Beispiels, wenn sie im Editor
        geöffnet sind.
        NOTE: Probleme beim "Aufräumen", Exceptions."""
        xmp_name = self.selected_example_data['example']
        file_url = QUrl(
            '{}/{}.ly'.format(self.config().project_root(), xmp_name))
        file_url.setScheme('file')
        doc = app.findDocument(file_url)
        if doc:
            self.mainwindow().closeDocument(doc)
        if self.selected_example_data['include']:
            include_url = QUrl(
                '{}/{}-include.ily'.format(
                    self.config().project_root(), xmp_name))
            include_url.setScheme('file')
            include_doc = app.findDocument(include_url)
            if include_doc:
                self.mainwindow().closeDocument(include_doc)
        self.mainwindow().setCurrentDocument(doc)

    def _example_file_names(self):
        xmp_name = self.selected_example_data['example']
        return ('{}/{}.ly'.format(self.config().project_root(), xmp_name),
            '{}/{}-include.ily'.format(self.config().project_root(), xmp_name))

    def _create_file_from_template(self, file_type, template_type, file_name):
        """Liest eine Template-Datei ein und erzeugt eine Arbeitsdatei."""
        xmp_name = self.selected_example_data['example']
        with open(os.path.join(self.config().project_root(), 'vorlage',
            '{}.ly'.format(template_type))) as f:
            template = f.read()
        with open(file_name, 'w') as f:
            f.write(template.replace('<<<example>>>', xmp_name))
        self.selected_example_data[file_type] = True

    def _create_file(self, file_type, template_type, file_name):
        """Erzeugt eine Arbeitsdatei nach Template und öffnet sie."""
        self._create_file_from_template(file_type, template_type, file_name)
        self.open_file()
        self.model.populate()

    def create_file(self):
        """Erzeuge eine neue Arbeitsdatei für ein System"""
        file_name, _ = self._example_file_names()
        self._create_file('file', 'ein-system', file_name)

    def create_file_2(self):
        """Erzeuge eine neue Arbeitsdatei für zwei Systeme."""
        file_name, _ = self._example_file_names()
        self._create_file('file', 'zwei-systeme', file_name)

    def _create_files(self, template_type):
        """Erzeuge Arbeits- und Include-Datei nach Template und öffne sie."""
        file_name, include_name = self._example_file_names()
        self._create_file_from_template('file', template_type, file_name)
        self._create_file_from_template('include', 'include', include_name)
        self.open_file()
        self.model.populate()

    def create_files(self):
        """Erzeuge Dateipaar für ein System."""
        self._create_files('ein-system')

    def create_files_2(self):
        """Erzeuge Dateipaar für zwei Systeme."""
        self._create_files('zwei-systeme')

    def create_include(self):
        """Erzeuge eine neue Include-Datei."""
        _, include_name = self._example_file_names()
        self._create_file('include', 'include', include_name)

    def open_file(self):
        """Öffnet die Datei(en) für das ausgewählte Beispiel.
        Wenn das Kontextmenü vom Include-File ausgelöst wird und dieses
        vorhanden ist, wird dieses zum aktiven Dokument gemacht,
        andernfalls das Haupt-Dokument."""
        file_name, include_name = self._example_file_names()
        file_url = QUrl(file_name)
        file_url.setScheme('file')
        doc = app.openUrl(file_url)
        if self.selected_example_data['include']:
            include_url = QUrl(include_name)
            include_url.setScheme('file')
            include_doc = app.openUrl(include_url)
            if self.selected_example_data['column'] == 2:
                doc = include_doc
        self.mainwindow().setCurrentDocument(doc)

    def show_manuscript(self):
        manuscript_viewer = panelmanager.manager(
            self.mainwindow()).panel_by_name('manuscript')

        # TODO: Load document

        xmp_name = self.selected_example_data['example']
        print("Show", xmp_name)
        if xmp_name.startswith('1756_erratum'):
            page = 265
        elif xmp_name.startswith('1756_tabelle'):
            page = 266
        else:
            reg = re.compile('1756_(\d+)_.*')
            match = reg.match(xmp_name)
            if not match:
                return
            page = int(match.group(1))
        manuscript_viewer.setCurrentPage(page)


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
