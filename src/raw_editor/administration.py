import sys
from PyQt5.QtWidgets import *
from rql_editor import RqlEditor
from settings import exception_dialog
from rawapi import new_raw_client


class ListTable(QTableWidget):
    def __init__(self, title):
        super(QTableWidget, self).__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels([title])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setFixedWidth(250)

    def setItems(self, items):
        self.setRowCount(len(items))
        for n, v in enumerate(items):
            self.setItem(n - 1, 1, QTableWidgetItem(v))


class ListEditorWidget(QDialog):
    def __init__(self, title):
        super(ListEditorWidget, self).__init__()
        self.setWindowTitle(title)
        self.setGeometry(300, 300, 1700, 700)
        hbox = QHBoxLayout()
        self.setLayout(hbox)
        self.client = new_raw_client()
        self.table = ListTable(title)
        hbox.addWidget(self.table)
        vbox = QVBoxLayout()
        # Button to delete views, packages or similar
        self.delete_btn = QPushButton('Delete')
        self.delete_btn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TrashIcon')))
        self.delete_btn.setMaximumWidth(60)
        self.delete_btn.clicked.connect(self._handle_delete)
        vbox.addWidget(self.delete_btn)
        # Editor to show code
        self.editor = RqlEditor()
        self.editor.setWrapMode(True)
        self.editor.setReadOnly(True)
        vbox.addWidget(self.editor)
        hbox.addLayout(vbox)
        self.table.itemClicked.connect(self._handle_clicked)
        self.refresh()

    @exception_dialog
    def refresh(self):
        self.editor.setText("")
        self.items = self.list_items()
        if self.items:
            self.table.setItems(self.items)
            self.table.selectRow(0)
            self._handle_clicked(self.table.item(0, 0))
        else:
            self.table.setItems(["No items found"])

    @exception_dialog
    def _handle_clicked(self, item):
        if self.items:
            self.current_name = item.text()
            self.item_clicked(item.text())

    @exception_dialog
    def _handle_delete(self, state):
        if self.items:
            self.delete_item(self.current_name)
            self.refresh()

    def closeEvent(self, evnt):
        # kills the undo process
        self.editor.stop()


    def item_clicked(self, item):
        raise NotImplementedError()

    def list_items(self):
        raise NotImplementedError()

    def delete_item(self, name):
        raise NotImplementedError()


class ViewsWindow(ListEditorWidget):
    def __init__(self):
        super(ViewsWindow, self).__init__("Views")

    def list_items(self):
        return self.client.views_list_names()

    def item_clicked(self, name):
        view = self.client.views_show(name)
        self.editor.setText(view['query'])

    def delete_item(self, name):
        self.client.views_drop(name)


class MaterializedViewsWindow(ListEditorWidget):
    def __init__(self):
        super(MaterializedViewsWindow, self).__init__("Materialized Views")

    def list_items(self):
        return self.client.materialized_views_list_names()

    def item_clicked(self, name):
        view = self.client.materialized_views_show(name)
        self.editor.setText(view['query'])

    def delete_item(self, name):
        self.client.materialized_views_drop(name)


class PackagesWindow(ListEditorWidget):
    def __init__(self):
        super(PackagesWindow, self).__init__("Packages")

    def list_items(self):
        return self.client.packages_list_names()

    def item_clicked(self, name):
        view = self.client.packages_show(name)
        self.editor.setText(view['query'])

    def delete_item(self, name):
        self.client.packages_drop(name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex1 = ViewsWindow()
    ex1.show()
    ex2 = PackagesWindow()
    ex2.show()
    ex3 = MaterializedViewsWindow()
    ex3.show()
    sys.exit(app.exec_())
