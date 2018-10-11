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
import re
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

def create_examples(examples, overview, widget):
    """Take a list of example names and produce all the relevant
    output files. 'widget' is the QTabWidget holding the
    example_widget and config_widget tabs. 'examples' is a string list.
    If 'overview' is either 'visible' or 'all' an overview PDF
    will be created after the examplese have been created."""
    dlg = ProcessDialog(examples, overview, widget)
    dlg.exec_()


TYPES = ['PDF', 'PNG300', 'PNG72', 'SVG']


# Classes to handle file conversions from PDF to other image formats.
# AbstractConversion and its descendants are used by Conversion.create()
# to create a job.Job object with the appropriate command.

class AbstractConversion(job.Job):


    def __init__(self, filename):
        directory, self.filename = os.path.split(filename)
        self.basename = os.path.splitext(self.filename)[0]
        super(AbstractConversion, self).__init__(self.conversion_command())
        self.set_directory(directory)

    def conversion_command(self):
        raise NotImplementedError


class PNGConversion(AbstractConversion):

    def __init__(self, filename):
        super(PNGConversion, self).__init__(filename)

    def conversion_command(self):
        cmd = ['convert',
               '-density',
               self.density(),
               self.filename,
               '{}-{}.png'.format(self.basename, self.resolution)]
        return cmd

    def density(self):
        return '{}x{}'.format(self.resolution, self.resolution)


class PNG300Conversion(PNGConversion):
    resolution = '300'


class PNG72Conversion(PNGConversion):
    resolution = '72'


class SVGConversion(AbstractConversion):

    def __init__(self, filename):
        super(SVGConversion, self).__init__(filename)

    def conversion_command(self):
        return ['pdftocairo',
               '-svg',
               self.filename,
               '{}.svg'.format(self.basename)]


class Conversion(QObject):

    classes = {
        'PNG300': PNG300Conversion,
        'PNG72': PNG72Conversion,
        'SVG': SVGConversion
    }

    @classmethod
    def create(cls, filename, type):
        return Conversion.classes[type](filename)


class AbstractJobHandler(QObject):
    """Manages an individual engraving/conversion job.

    Constructs the job and keeps the connection between the
    JobQueue and the GUI. Responsible for cleaning up temporary
    files and for notifying the GUI about the state.

    """

    def __init__(self, dialog, example):
        super(AbstractJobHandler, self).__init__()
        self.dialog = dialog
        self.example = example
        self.project_root = dialog.project_root
        self.export_directory = dialog.export_directory
        self._job = None

    def cleanup_files(self):
        """Remove intermediate files. May be implemented in subclasses."""
        pass

    def _create_job(self):
        """Create the actual job.Job instance.
        Must be implemented in subclasses."""
        raise NotImplementedError

    def enqueue(self):
        """Add the current (newly created) job to the queue."""
        self.dialog.queue.add_job(self.job())

    def job(self):
        """Return the job. If it isn't available yet, create a
        job and configure it for the current engraving/conversion."""
        if not self._job:
            self._create_job()
            self._job.started.connect(self.slot_job_started)
            self._job.done.connect(self.slot_job_done)
        return self._job

    def slot_job_done(self):
        """Process results after completion of the job."""
        raise NotImplementedError

    def slot_job_started(self):
        """Update the progress dialog."""
        self.dialog.job_started(self, self.type)


class ConversionJobHandler(AbstractJobHandler):
    """Handle a file format conversion."""

    def __init__(self, dialog, file, type):
        self.filename = file
        example = os.path.splitext(os.path.basename(file))[0]
        example = re.match('1756_\d\d\d_\d+', example).group()
        super(ConversionJobHandler, self).__init__(dialog, example)
        self.type = type

    def _create_job(self):
        """Ask the Conversion.create factory function to create
        an AbstractConversion instance depending on the format type."""
        self._job = Conversion.create(self.filename, self.type)

    def slot_job_done(self):
        """Update dialog."""
        self.dialog.job_done(self)


class LilyPondJobHandler(AbstractJobHandler):
    """Handle a LilyPond engraving Job."""

    def __init__(self, dialog, example):
        super(LilyPondJobHandler, self).__init__(dialog, example)
        self._result_files = []
        self.openLilyLib_root = dialog.openLilyLib_root
        self.type = 'PDF'

    def _create_job(self):
        """Create the job.lilypond.LilyPondJob to engrave
        the given example."""
        example = self.example
        self._job = j = job.lilypond.PublishJob(
            QUrl.fromLocalFile(
            os.path.join(self.project_root, '{}.ly'.format(example))),
            title='{}: pdf'.format(example))
        j.set_d_option('delete-intermediate-files')
        j.set_d_option('systems')
        j.add_include_path(self.project_root)
        j.add_include_path(self.openLilyLib_root)
        j.add_argument('--output={}'.format(os.path.join(
            self.export_directory,
            '{}'.format(example))))
        j.set_backend_args(['-dcrop'])

    def cleanup_files(self):
        """Cleanup of the temporary files produced by the LilyPond run,
        only retaining the PDF and the <example>-systems.count files."""
        for file in self.created_files():
            base_name, ext = os.path.splitext(file)
            file_name = os.path.join(self.export_directory, file)
            if not ext in ['.pdf', '.count']:
                os.remove(file_name)
            elif ext == '.pdf':
                self._result_files.append(file_name)

    def created_files(self):
        """Returns a list of all files in the export directory
        that start with the current job name."""
        files = os.listdir(self.export_directory)
        return [file for file in files if file.startswith(self.example)]

    def slot_job_done(self):
        """Remove unneeded files and update dialog."""
        self.cleanup_files()
        self.dialog.add_result_files(self._result_files)
        self.dialog.job_done(self)


class ProcessDialog(widgets.dialog.Dialog):
    """Dialog displaying the progress of the batch compilation.
    Provides interfaces for pausing, resuming and aborting the process.

    TODO: Move this to the (non-modal) Tool to enable continuing to
    work in the editor during that process."""

    def __init__(self, examples, overview, widget):
        super(ProcessDialog, self).__init__(
            parent=widget,
            buttons=('cancel', 'ok',),
            title="Erzeuge Notenbeispiel(e)",
            )
        self.overview = overview
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
            num_runners=s.value('num-runners', 1, int))
        self.queue.idle.connect(self.enqueue_conversions)
        oll_root_file = os.path.join(self.project_root, 'openlilylib-root')
        with open(oll_root_file) as f:
            self.openLilyLib_root = f.read().strip().strip('\n')

        self._job_count = 0
        self._skipped_count = 0
        self._jobs_done = 0
        self._result_files = []

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
            self.button('cancel').clicked.disconnect()
            self.button('cancel').clicked.connect(self.abort)
            self.button('ok').setEnabled(False)
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

    def add_result_files(self, files):
        """Add files to the list of result files. Needed to
        generate the list of conversion jobs."""
        self._result_files.extend(
            [file for file in files if file.endswith('.pdf')])

    def create_jobs(self):
        """Generate the LilyPond jobs to engrave all requested examples."""
        type_cnt = len(TYPES)
        model = self.results_view.model()
        for i in range(model.rowCount()):
            example = model.verticalHeaderItem(i).text()
            if self.up_to_date(example):
                self._skipped_count += type_cnt
                for type in TYPES:
                    checkbox = self.checkbox({
                        'example': example,
                        'type': type})
                    checkbox.setCheckState(2)
                    checkbox.setForeground(QBrush(QColor(0, 196, 255)))
            else:
                self._job_count += type_cnt
                # Storing references in a list,
                # necessary to keep the objects alive.
                self._job_handlers.append(LilyPondJobHandler(self, example))
                self._job_handlers[-1].enqueue()

    def create_overview_pdf(self):

        filtered = self.overview == 'visible'
        visible_examples = self.parent().example_names(visible_only=True)

        tex = [
            '\\documentclass[b5paper]{scrartcl}',
            '\\usepackage{graphicx}',
            '\\usepackage[margin=1cm]{geometry}'
            '\\setlength{\\parindent}{0pt}',
            '\\begin{document}',
            '\\section*{Leopold Mozart: Violinschule (1756) -- Notenbeispiele}',
            'Dieses Dokument enthält die bereits gesetzten Notenbeispiele',
            'aus der Violinschule von Leopold Mozart (Ausgabe 1756).'
        ]
        if filtered:
            file_filter = self.parent().cb_filter_file.checkState()
            file_input = self.parent().cb_filter_input.checkState()
            file_review = self.parent().cb_filter_review.checkState()
            file_approved = self.parent().cb_filter_approved.checkState()
            if file_filter + file_input + file_review + file_approved > 0:
                states = ['egal', 'nein', 'ja']

                tex.extend([
                    'Die Auswahl ist gefiltert nach folgenden Kriterien:',
                    '',
                    '\\begin{itemize}',
                    '\\itemsep 0em',
                ])
                if file_filter:
                    tex.append('\\item Datei vorhanden: {}'.format(
                        states[file_filter]))
                if file_input:
                    tex.append('\\item Eingegeben: {}'.format(
                        states[file_input]))
                if file_review:
                    tex.append('\\item Zur Abnahme: {}'.format(
                        states[file_review]))
                if file_approved:
                    tex.append('\\item Abgenommen: {}'.format(
                        states[file_approved]))
                tex.append('\\end{itemize}')

        tex.extend([
            'Farbig markierte Elemente verweisen auf Annotationen,'
            'die im Quelltext des jeweiligen Beispiels nachgelesen werden',
            'können. Für die Publikation wird die Farbverwendung einfach',
            'deaktiviert. \\emph{Dunkelgrün} steht für kritische Anmerkungen,',
            '\\emph{Hellgrün} für noch zu entscheidende inhaltliche Fragen,',
            'und \\emph{Rot} verweist auf zu lösende technische Probleme.\par'
        ])

        list_file = os.path.join(self.project_root, 'vorlage', 'beispiel-liste')
        re_heading = re.compile('(\**) (.*)')
        with open(list_file) as f:
            input_list = f.read().split('\n')
        for line in input_list:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re_heading.match(line)
            if match:
                # Handle top/second-level headings
                level, title = match.groups()
                if level == '*':
                    tex.append('\\subsection*{{{}}}'.format(title))
                else:
                    tex.append('\\subsubsection*{{{}}}'.format(title))
            else:
                # Handle single example
                current_example = line.split()[0]
                current_example_tex = current_example.replace('_', '\\_')
                if filtered and not current_example in visible_examples:
                    tex.append('\\texttt{{{}}} -- gefiltert\\par'.format(
                        current_example_tex))
                elif not os.path.isfile(
                    os.path.join(self.export_directory, '{}-systems.count'.format(
                    current_example))):
                    tex.append('\\texttt{{{}}} -- nicht vorhanden\\par'.format(
                        current_example_tex))
                else:
                    count_file = os.path.join(self.export_directory,
                        '{}-systems.count'.format(current_example))
                    with open(count_file) as f:
                        system_count = int(f.read())
                    tex.append('\\texttt{{{}}} -- {} Akkolade(n)'.format(
                        current_example_tex, system_count))
                    tex.append('\\par\\nobreak\\bigskip\\nobreak')
                    for i in range(system_count):
                        tex.extend([
                            '\\includegraphics{{{}-{}.pdf}}\\par'.format(
                                current_example, i + 1),
                            '\\medskip'
                        ])

        tex.append('\\end{document}\n')
        self.overview_file = os.path.join(self.export_directory,
            'Notenbeispiele_gefiltert.tex' if filtered
            else 'Notenbeispiele.tex')
        with open(self.overview_file, 'w') as f:
            f.write('\n'.join(tex))

        self.queue.idle.disconnect(self.slot_conversions_completed)
        self.queue.idle.connect(self.slot_overview_created)
        j = job.Job(['pdflatex', self.overview_file])
        j.set_directory(self.export_directory)
        self.queue.add_job(j)
        self.setMessage(self.message + '\nErzeuge PDF-Übersicht.')

    def enqueue_conversions(self):
        """Triggered when the queue is getting IDLE (for the first time).
        Now all scores have been engraved to PDF, and we can create
        and enqueue the jobs to convert the resulting files to the
        additional image formats"""
        self.queue.idle.disconnect(self.enqueue_conversions)
        self.queue.idle.connect(self.slot_conversions_completed)
        self._job_handlers = []
        # temorarily stop the queue to avoid any race conditions
        self.queue.pause()
        for file in self._result_files:
            for type in [type for type in TYPES if type != 'PDF']:
                self._job_handlers.append(ConversionJobHandler(self, file, type))
                self._job_handlers[-1].enqueue()
        self.queue.resume()

    def up_to_date(self, example):
        """Return True if the file modification time of the
        output file is later than the input file.
        NOTE: This only takes care about the '<example>.pdf' file,
        the other example types are ignored. So this is a check for
        current-ness of examples but doesn't notice files that have
        been deleted externally."""

        # TODO:
        # This fails when switching Git branches updates the input
        # files' modification date, resulting in unnecessary recompilations.
        # There should be better heuristics checking against Git status of
        # the input files.
        outfile = os.path.join(
            self.export_directory,
            '{}.pdf'.format(example))
        if not os.path.isfile(outfile):
            return False
        omod = QFileInfo(outfile).fileTime(QFileDevice.FileModificationTime)
        infile = os.path.join(
            self.project_root,
            '{}.ly'.format(example))
        imod = QFileInfo(infile).fileTime(QFileDevice.FileModificationTime)
        return omod >= imod

    def slot_conversions_completed(self):
        """Triggered when the queue reaches IDLE for the second
        time, i.e. after converting all example PDFs to the other formats."""
        self._ticker.stop()
        ac = self.widget.action_collection
        ac.mozart_process_abort.setEnabled(False)
        ac.mozart_process_resume.setEnabled(False)
        ac.mozart_process_pause.setEnabled(False)
        self.final_message()
        if self.overview:
            self.create_overview_pdf()
        else:
            self.button('cancel').setEnabled(False)
            self.button('ok').setEnabled(True)

    def slot_overview_created(self):
        """Triggered when a final overview PDF has been created."""
        self.setMessage(self.message + '\nAbgeschlossen.')
        self.button('cancel').setEnabled(False)
        self.button('ok').setEnabled(True)
        result_file = '{}.pdf'.format(os.path.splitext(self.overview_file)[0])
        import helpers
        helpers.openUrl(QUrl.fromLocalFile(result_file))


    def checkbox(self, jobinfo):
        """"Determine the "results view" checkbox corresponding
        tot he given jobinfo."""
        if isinstance(jobinfo, AbstractJobHandler):
            example = jobinfo.example
            type = jobinfo.type
        else:
            example = jobinfo['example']
            type = jobinfo['type']
        return self.results_view.model().invisibleRootItem().child(
            self.examples.index(example),
            TYPES.index(type))

    def job_done(self, jobinfo):
        """Update the results View after the job has been completed."""
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

    def job_started(self, jobinfo, type='PDF'):
        self.activities_view.update_runner(
            jobinfo.job().runner().index(),
            jobinfo.example,
            type)
        check_box = self.checkbox(jobinfo)
        check_box.setCheckState(1)

    def final_message(self):
        self.message = ("{}\n" +
            "{} Jobs in {} erledigt.\n" +
            "{} aktuelle Jobs übersprungen").format(
                self.status,
                self._jobs_done,
                job.Job.elapsed2str(time.time() - self.queue._starttime),
                self._skipped_count)
        self.setMessage(self.message)

    def update_message(self):
        """Aktualisiere die Status-Message."""
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
        self.setModel(QStandardItemModel())
        self.model().setHorizontalHeaderLabels(TYPES)
        for col in range(len(TYPES)):
            self.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents)

        root = self.model().invisibleRootItem()
        for example in examples:
            items = []
            for type in TYPES:
                items.append(QStandardItem())
                items[-1].setCheckable(False)
                items[-1].setCheckState(Qt.Unchecked)
            root.appendRow(items)
        self.model().setVerticalHeaderLabels(examples)
