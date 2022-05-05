import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from rql_editor import RqlEditor
from query_results import QueryView

from query_client import AsyncQueryClient
from settings import *
from administration import *
from theme import *
import json

import resources


class MainWindow(QMainWindow):

    def __init__(self, conf, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        if not conf:
            conf = dict(theme=dict(Widgets=None, Editor=None, QueryView=None))
        layout = QVBoxLayout()
        self.editor = RqlEditor(conf['theme']['Editor'])
        self.query_results = QueryView(conf['theme']['QueryView'])

        self.init_client()

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None

        layout.addWidget(self.editor)
        layout.addWidget(self.query_results)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        open_file_action = QAction(QIcon(':images/blue-folder-open-document.png'), "Open file...", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        save_file_action = QAction(QIcon(':images/disk.png'), "Save", self)
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.file_save)

        saveas_file_action = QAction(QIcon(':images/disk--pencil.png'), "Save As...", self)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_save_as)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(QIcon(':images/arrow-curve-180-left.png'), "Undo", self)
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.editor.undo)
        edit_toolbar.addAction(undo_action)
        edit_menu.addAction(undo_action)

        redo_action = QAction(QIcon(':images/arrow-curve.png'), "Redo", self)
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(':images/scissors.png'), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(QIcon(':images/document-copy.png'), "Copy", self)
        copy_action.setStatusTip("Copy selected text")
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(QIcon(':images/clipboard-paste-document-text.png'), "Paste", self)
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(QIcon(':images/selection-input.png'), "Select all", self)
        select_action.setStatusTip("Select all text")
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(QIcon(':images/arrow-continue.png'), "Wrap text to window", self)
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        query_toolbar = QToolBar("Query")
        query_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(query_toolbar)
        query_menu = self.menuBar().addMenu("Query")

        run_query_action = QAction(QIcon(':images/play.png'), "Run query", self)
        run_query_action.setStatusTip("Run query")
        run_query_action.triggered.connect(self.run_query)
        query_toolbar.addAction(run_query_action)
        query_menu.addAction(run_query_action)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.run_query)

        validate_query_action = QAction(QIcon(':images/validate.png'), "Validate query", self)
        validate_query_action.setStatusTip("Validate query")
        validate_query_action.triggered.connect(self.validate_query)
        query_toolbar.addAction(validate_query_action)
        query_menu.addAction(validate_query_action)
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+Return"), self)
        shortcut.activated.connect(self.validate_query)

        stop_query_action = QAction(QIcon(':images/stop.png'), "Stop query", self)
        stop_query_action.setStatusTip("Stop query")
        stop_query_action.triggered.connect(self.stop_query)
        query_toolbar.addAction(stop_query_action)
        query_menu.addAction(stop_query_action)

        publish_query_action = QAction(QIcon(':images/cloud-arrow.png'), "Publish query", self)
        publish_query_action.setStatusTip("Publish query")
        publish_query_action.triggered.connect(self.publish_query)
        query_toolbar.addAction(publish_query_action)
        query_menu.addAction(publish_query_action)

        self.animation1 = QLabel(self.editor)
        self.animation1.setScaledContents(True)
        self.animation1.hide()
        self.movie1 = QMovie(':images/loading1.gif')
        self.animation1.setMovie(self.movie1)

        self.animation2 = QLabel(self.editor)
        self.animation2.setScaledContents(True)
        self.animation2.hide()
        self.movie2 = QMovie(':images/loading2.gif')
        self.animation2.setMovie(self.movie2)

        administration_menu = self.menuBar().addMenu("Administration")
        views_action = QAction("Views", self)
        views_action.triggered.connect(self.administration_views)
        administration_menu.addAction(views_action)

        packages_action = QAction("Packages", self)
        packages_action.triggered.connect(self.administration_packages)
        administration_menu.addAction(packages_action)

        mt_views_action = QAction("Materialized Views", self)
        mt_views_action.triggered.connect(self.administration_mt_views)
        administration_menu.addAction(mt_views_action)

        settings_menu = self.menuBar().addMenu("Settings")
        s3_buckets_action = QAction("S3 Buckets", self)
        s3_buckets_action.triggered.connect(self.s3_settings)
        settings_menu.addAction(s3_buckets_action)

        rdbms_action = QAction("RDBMS Servers", self)
        rdbms_action.triggered.connect(self.rdbms_settings)
        settings_menu.addAction(rdbms_action)

        http_action = QAction("HTTP Auth", self)
        http_action.triggered.connect(self.http_settings)
        settings_menu.addAction(http_action)

        self.update_title()
        self.show()

    def init_client(self):
        self.client = AsyncQueryClient(self)
        self.client.query_done.connect(self.query_done)
        self.client.query_validated.connect(self.query_validated)
        self.client.error.connect(self.query_error)

    def start_spin(self):
        self.editor.setEnabled(False)
        # If the editor has a light color paper load animation1
        # if it is darker loads animation 2
        paper_color = self.editor.lexer.defaultPaper()
        if (paper_color.rgb() >= 4286578687):
            animation = self.animation1
            movie = self.movie1
        else:
            animation = self.animation2
            movie = self.movie2

        x1 = int(self.editor.width() / 2 - 50)
        animation.setGeometry(x1, 150, 150, 150)
        animation.setVisible(True)
        movie.start()

    def stop_spin(self):
        self.movie1.stop()
        self.animation1.hide()
        self.movie2.stop()
        self.animation2.hide()
        self.editor.setEnabled(True)

    def run_query(self):
        if self.client.executing_cmd:
            self.status.showMessage('another command is executing', 5000)
            return
        self.start_spin()
        query = self.editor.text()
        self.client.query(query)

    def administration_views(self):
        w = ViewsWindow()
        # w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def administration_packages(self):
        w = PackagesWindow()
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def administration_mt_views(self):
        w = MaterializedViewsWindow()
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def s3_settings(self):
        w = S3SettingsWindow()
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def rdbms_settings(self):
        w = RdbmsSettingsWindow()
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def http_settings(self):
        w = HttpSettingsWindow()
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def publish_query(self):
        w = PublishWindow(self.editor.text())
        w.setWindowModality(Qt.ApplicationModal)
        w.exec_()

    def validate_query(self):
        if self.client.executing_cmd:
            self.status.showMessage('another command is executing', 5000)
            return
        self.start_spin()
        query = self.editor.text()
        self.client.validate(query)

    def query_done(self, tipe, data):
        self.stop_spin()
        if tipe['type'] == 'collection' and data is not None:
            data_array = []
            try:
                for n in range(100):
                    data_array.append(data.next())
                self.status.showMessage('showing only 100 lines', 10000)
            except StopIteration:
                pass
            data.close()
            self.query_results.show_data(tipe, data_array)
        else:
            self.query_results.show_data(tipe, data)

    def query_error(self, msg):
        self.stop_spin()
        self.query_results.show_error_text(msg)

    def query_validated(self, data):
        self.stop_spin()
        if data['errors']:
            self.query_results.show_error_text(str(data['errors']))
        else:
            self.query_results.show_text(data['type'])

    def stop_query(self):
        if self.client.executing_cmd:
            self.client.stop()
            self.client.setParent(None)
            # If the client is busy executing something then tries kill it create a new instance
            self.init_client()

        self.stop_spin()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Text documents (*.txt);All files (*.*)")

        try:
            with open(path, 'rU') as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_save_as()

        text = self.editor.text()
        try:
            with open(self.path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Text documents (*.rql);All files (*.*)")
        text = self.editor.text()

        if not path:
            # If dialog is cancelled, will return ''
            return

        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def update_title(self):
        self.setWindowTitle("%s - Query-Client" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setWrapMode(False if self.editor.wrapMode() else True)


def get_config():
    conf_file_path = 'conf.json'
    if os.path.exists(conf_file_path):
        # opening default theme
        with open(conf_file_path) as f:
            conf = json.load(f)
        return dict(theme=load_theme(conf['theme']))
    else:
        return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Query editor")

    conf = get_config()
    if conf['theme']:
        palette = QPalette()
        for name, value in conf['theme']["Widgets"].items():
            palette.setColor(QPalette.__dict__[name], value)
        app.setPalette(palette)

    window = MainWindow(conf)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
