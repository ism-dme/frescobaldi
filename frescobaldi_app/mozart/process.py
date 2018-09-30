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
Compile music examples for the Leopold Mozart Violin School (1756) edition.
Use the multithreaded job queue to compile in parallel and provide a
progress dialog indicating activity, providing controls to abort, pause and
resume the process.
"""

import os
import time

from PyQt5.QtCore import (
    QFileDevice,
    QFileInfo,
    QObject,
    QSettings,
    Qt,
    QTimer,
    QUrl
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QStandardItem,
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QGridLayout,
    QHeaderView,
    QTableView,
    QToolBar
)

import job.queue
from job.queue import QueueMode, QueueStatus
import signals
import widgets.dialog

def create_examples(examples, widget):
    """Take a list of example names and produce all the relevant
    output files. 'widget' is the QTabWidget holding the
    example_widget and config_widget tabs. 'examples' is a string list."""
    dlg = ProcessDialog(examples, widget)
    dlg.exec_()


class JobHandler(QObject):
    """Manages an individual LilyPond job.

    Constructs the LilyPond job and keeps the connection between
    the JobQueue and the GUI. Responsible for cleaning up temporary
    files and for notifying the GUI about the state.

    """

    def __init__(self, dialog, example, type):
        super(JobHandler, self).__init__()
        self.dialog = dialog
        self.example = example
        self.type = type
        self.basename = '{}-{}'.format(example, type)
        self.project_root = dialog.project_root
        self.export_directory = dialog.export_directory
        self.openLilyLib_root = dialog.openLilyLib_root
        self._backend_args = {
            'PDF': ['-dcrop'],
            'PNG': ['-dcrop', '--png', '-dresolution=300'],
            'SVG': ['-dcrop', '-dbackend=svg']
        }
        self._job = None

    def cleanup_files(self):
        """Cleanup of the temporary files produced by the LilyPond run,
        only retaining the cropped output file.
        Also rename the resulting file to the canonical template."""
        ext = self.type.lower()
        for file in self.export_files():
            file_name = os.path.join(self.export_directory, file)
            if not file.endswith('cropped.{}'.format(ext)):
                os.remove(file_name)
            else:
                os.rename(file_name,
                    os.path.join(self.export_directory, '{}.{}'.format(
                        self.example, ext)))

    def enqueue(self):
        """Add the current (newly created) job to the queue."""
        j = self.job()
        self.dialog.queue.add_job(j)

    def export_files(self):
        """Returns a list of all files in the export directory
        that start with the current job's example/type signature."""
        files = os.listdir(self.export_directory)
        return [file for file in files if file.startswith(self.basename)]

    def job(self):
        """Return the job. If it isn't available yet, create a LilyPond
        job and configure it for the current example/type."""
        if not self._job:
            example = self.example
            type = self.type
            self._job = j = job.lilypond.PublishJob(
                QUrl.fromLocalFile(
                os.path.join(self.project_root, '{}.ly'.format(example))),
                title='{}: {}'.format(example, type))
            j.set_d_option('delete-intermediate-files')
            j.add_include_path(self.project_root)
            j.add_include_path(self.openLilyLib_root)
            j.add_argument('--output={}'.format(os.path.join(
                self.export_directory,
                '{}-{}'.format(example, type))))
            j.set_backend_args(self._backend_args[type])
            j.started.connect(self.slot_job_started)
            j.done.connect(self.slot_job_done)
        return self._job

    def slot_job_done(self):
        """Process results after completion of the job."""
        self.dialog.job_done(self)
        self.cleanup_files()

    def slot_job_started(self):
        """Update the progress dialog."""
        self.dialog.job_started(self)


class ProcessDialog(widgets.dialog.Dialog):
    """Dialog displaying the progress of the batch compilation.
    Provides interfaces for pausing, resuming and aborting the process.

    TODO: Move this to the (non-modal) Tool to enable continuing to
    work in the editor during that process."""

    def __init__(self, examples, widget):
        super(ProcessDialog, self).__init__(
            parent=widget.mainwindow(),
            buttons=('cancel', 'ok',),
            title="Erzeuge Notenbeispiel(e)",
            )
        self.widget = widget
        ac = widget.action_collection

        self.status = "Erzeugen erfolgreich"
        self.examples = examples
        self._job_handlers = []
        s = QSettings()
        s.beginGroup('mozart')
        self.project_root = s.value('root')
        self.export_directory = s.value('export')
        self.queue = job.queue.JobQueue(
            num_runners=s.value('num-runners', 1, int),
            queue_mode=QueueMode.SINGLE)

        oll_root_file = os.path.join(self.project_root, 'openlilylib-root')
        with open(oll_root_file) as f:
            self.openLilyLib_root = f.read().strip().strip('\n')

        self._job_count = 0
        self._skipped_count = 0
        self._jobs_done = 0

        self._ticker = QTimer()
        self._ticker.setInterval(1000)
        self._ticker.timeout.connect(self.update_message)

        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QGridLayout()
        self.mainWidget().setLayout(layout)

        self.toolbar = QToolBar(self)
        self.toolbar.addAction(ac.mozart_process_abort)
        ac.mozart_process_abort.triggered.connect(self.abort)
        ac.mozart_process_abort.setEnabled(True)
        self.toolbar.addAction(ac.mozart_process_pause)
        ac.mozart_process_pause.triggered.connect(self.pause)
        ac.mozart_process_pause.setEnabled(True)
        self.toolbar.addAction(ac.mozart_process_resume)
        ac.mozart_process_resume.triggered.connect(self.resume)
        ac.mozart_process_resume.setEnabled(False)

        self.activities_view = ActivitiesView(self)
        self.results_view = ResultsView(examples, self)
        layout.addWidget(self.toolbar, 0, 0, 1, 2)
        layout.addWidget(self.activities_view, 1, 0, 1, 1)
        layout.addWidget(self.results_view, 1, 1, 1, 1)

        self.create_jobs()
        if self._job_handlers:
            self.queue.finished.connect(self.slot_queue_finished)
            self.queue.start()
            self._ticker.start()
        else:
            # All examples are up-to-date
            self.setMessage("Alle Beispiele waren aktuell.")

    def abort(self):
        self.status = "Abbruch durch Benutzer"
        ac = self.widget.action_collection
        ac.mozart_process_abort.setEnabled(False)
        ac.mozart_process_resume.setEnabled(False)
        ac.mozart_process_pause.setEnabled(False)
        self._ticker.stop()
        self.queue.abort(force=True)

    def pause(self):
        ac = self.widget.action_collection
        ac.mozart_process_abort.setEnabled(True)
        ac.mozart_process_resume.setEnabled(True)
        ac.mozart_process_pause.setEnabled(False)
        self._ticker.stop()
        self.queue.pause()

    def resume(self):
        ac = self.widget.action_collection
        ac.mozart_process_abort.setEnabled(True)
        ac.mozart_process_resume.setEnabled(False)
        ac.mozart_process_pause.setEnabled(True)
        self._ticker.start()
        self.queue.resume()

    def create_jobs(self):
        """Generate the ."""
        model = self.results_view.model()
        types = ['PDF', 'PNG', 'SVG']
        for i in range(model.rowCount()):
            example = model.verticalHeaderItem(i).text()
            for type in types:
                if not self.up_to_date(example, type):
                    self._job_count += 1
                    # Storing references in a list,
                    # necessary to keep the objects alive.
                    self._job_handlers.append(JobHandler(self, example, type))
                    self._job_handlers[-1].enqueue()
                else:
                    self._skipped_count += 1
                    checkbox = self.checkbox({
                        'example': example,
                        'type': type})
                    checkbox.setCheckState(2)
                    checkbox.setForeground(QBrush(QColor(0, 196, 255)))

    def up_to_date(self, example, type):
        """Return True if the file modification time of the
        output file is later than the input file."""

        # TODO:
        # This fails when switching Git branches updates the input
        # files' modification date, resulting in unnecessary recompilations.
        # There should be better heuristics checking against Git status of
        # the input files.
        outfile = os.path.join(
            self.export_directory,
            '{}.{}'.format(example, type.lower()))
        if not os.path.isfile(outfile):
            return False
        omod = QFileInfo(outfile).fileTime(QFileDevice.FileModificationTime)
        infile = os.path.join(
            self.project_root,
            '{}.ly'.format(example))
        imod = QFileInfo(infile).fileTime(QFileDevice.FileModificationTime)
        return omod >= imod

    def slot_queue_finished(self):
        print("Queue finished")
        self._ticker.stop()
        ac = self.widget.action_collection
        ac.mozart_process_abort.setEnabled(False)
        ac.mozart_process_resume.setEnabled(False)
        ac.mozart_process_pause.setEnabled(False)
        self.final_message()

    def checkbox(self, jobinfo):
        if isinstance(jobinfo, JobHandler):
            example = jobinfo.example
            type = jobinfo.type
        else:
            example = jobinfo['example']
            type = jobinfo['type']
        return self.results_view.model().invisibleRootItem().child(
            self.examples.index(example),
            self.results_view.types.index(type)
        )

    def job_done(self, jobinfo):
        check_box = self.checkbox(jobinfo)
        if self.queue.state() == QueueStatus.ABORTED:
            check_box.setCheckState(1)
            check_box.setForeground(QBrush(QColor(10, 0, 128)))
            return
        self._jobs_done += 1
        self.update_message()
        self.activities_view.stop_runner(
            jobinfo.job().runner().index())
        j = jobinfo.job()
        if j.success:
            check_box.setCheckState(2)
        else:
            check_box.setCheckState(1)
            check_box.setForeground(QBrush(QColor(255, 0, 0)))
            log = [line[0] for line in j.history()]
            for line in log:
                print(line)
            #TODO: log speichern und im GUI zugänglich machen.
            #TODO: Von hier aus in Editor öffnen

    def job_started(self, jobinfo):
        self.activities_view.update_runner(
            jobinfo.job().runner().index(),
            jobinfo.example,
            jobinfo.type)
        check_box = self.checkbox(jobinfo)
        check_box.setCheckState(1)


    def final_message(self):
        self.setMessage(("{}\n" +
            "{} Jobs in {} erledigt.\n" +
            "{} aktuelle Jobs übersprungen").format(
                self.status,
                self._jobs_done,
                job.Job.elapsed2str(time.time() - self.queue._starttime),
                self._skipped_count
            ))

    def update_message(self):
        """Aktualisiere die Status-Message."""
        print("Update")
        self.message = "Bearbeitung: {} | {} ({}) Jobs erledigt."
        self.setMessage(self.message.format(
            job.Job.elapsed2str(int(time.time() - self.queue._starttime)),
            self._jobs_done,
            self._job_count))


class ActivitiesView(QTableView):
    """Fortschrittsanzeige der verschiedenen Runner."""
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
        """Erzeuge die initialen QStandardItems."""
        root = self.model().invisibleRootItem()
        for i in range(num_runners):
            root.appendRow([QStandardItem('--'), QStandardItem('--')])

    def stop_runner(self, runner):
        self.update_runner(runner, '--', '--')

    def update_runner(self, runner, example, type):
        """Zeige Beispiel und Typ in einem Runner an."""
        parent = self.model().invisibleRootItem()
        parent.child(runner, 0).setText(example)
        parent.child(runner, 1).setText(type)


class ResultsView(QTableView):
    """Stellt die Ergebnisse in einer Tabelle dar und
    hält sie in einem Datenmodell vor."""

    def __init__(self, examples, parent=None):
        super(ResultsView, self).__init__(parent)
        self.examples = examples
        self.types = ['PDF', 'PNG', 'SVG']
        self.setModel(QStandardItemModel())
        self.model().setHorizontalHeaderLabels(self.types)
        for col in range(len(self.types)):
            self.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents)

        root = self.model().invisibleRootItem()
        for example in examples:
            items = []
            for type in self.types:
                items.append(QStandardItem())
                items[-1].setCheckable(False)
                items[-1].setCheckState(Qt.Unchecked)
            root.appendRow(items)
        self.model().setVerticalHeaderLabels(examples)
