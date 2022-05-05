from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QSize
import sys
import os

default_theme = {
    'NullColor': QColor("#7f7f7f"),
    'StringColor': QColor("#9a2200"),
    'NumericTypeColor': QColor("#004f00"),
    'TemporalColor': QColor("#004f00"),
    'DefaultTypeColor': QColor("#00008f"),
    'QueryErrorTextColor': QColor('#8f0000'),
    'RecordFieldColor': QColor("#000000"),
    'RecordInnerColor': QColor("#7f7f7f"),
    'CollectionIndexColor': QColor("#5f0000"),
    'CollectionInnerColor': QColor("#7f7f7f"),
}


def get_type_brush(tipe, theme):
    if tipe['type'] == 'string':
        return QBrush(theme['StringColor'])
    elif tipe['type'] in ['date', 'time', 'timestamp', 'interval']:
        return QBrush(theme['TemporalColor'])
    elif tipe['type'] in ['int', 'long', 'short', 'byte', 'float', 'double', 'decimal']:
        return QBrush(theme['NumericTypeColor'])
    else:
        return QBrush(theme['DefaultTypeColor'])


class QueryView(QWidget):

    def __init__(self, theme=None, parent=None):
        super(QueryView, self).__init__(parent)

        if theme:
            self.theme = theme
        else:
            self.theme = default_theme

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(200, 200)
        # widget to show query results (either tree-view or table-view)
        self.results = None

        # text widget to show errors
        self.textbox = QPlainTextEdit(self)
        self.textbox.setReadOnly(True)

        self.layout.addWidget(self.textbox)

    def clear_results(self):
        if self.results:
            self.results.hide()
            self.results.setParent(None)

    def show_data(self, tipe, data):
        self.textbox.hide()
        self.clear_results()
        if self.is_tabular(tipe):
            self.results = QueryTableView(tipe, data, parent=self, theme=self.theme)
        else:
            self.results = QueryTreeView(tipe, data, parent=self, theme=self.theme)
            self.results.tree.setColumnWidth(0, self.width() / 2)
        self.layout.addWidget(self.results)

    def show_text(self, text):
        self.clear_results()
        self.textbox.setStyleSheet("QPlainTextEdit{font-size: 16px}")
        self.textbox.document().setPlainText(text)
        self.textbox.show()

    def show_error_text(self, text):
        self.clear_results()
        qcolor = self.theme['QueryErrorTextColor']
        color = hex(qcolor.rgb()).replace("0x", "#")
        self.textbox.setStyleSheet("QPlainTextEdit{color: %s; font-size: 16px}" % color)
        self.textbox.document().setPlainText(text)
        self.textbox.show()

    def is_tabular(self, tipe):
        def is_primitive(tipe):
            primitives = ['string', 'int', 'long', 'short', 'byte', 'float',
                          'double', 'decimal', 'date', 'time', 'null',
                          'timestamp', 'interval', 'bool']
            if tipe['type'] in primitives:
                return True
            else:
                return False

        def record_of_primitives(tipe):
            for att in tipe['atts']:
                if not is_primitive(att['type']):
                    return False
            return True

        if is_primitive(tipe):
            return True
        elif tipe['type'] == 'collection':
            inner = tipe['inner']
            if is_primitive(inner):
                return True
            elif inner['type'] == 'record':
                return record_of_primitives(inner)
            else:
                return False
        elif tipe['type'] == 'record':
            return record_of_primitives(tipe)
        else:
            return False


class QueryTableView(QTreeWidget):
    def __init__(self, tipe, data, theme=None, parent=None, ):
        super(QueryTableView, self).__init__(parent)

        if theme:
            self.theme = theme
        else:
            self.theme = default_theme
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)
        self.setAlternatingRowColors(True)

        self.setHeaderLabels(self.get_header(tipe))
        if tipe['type'] == 'collection' and data is not None:
            for obj in data:
                self.add_row(tipe['inner'], obj)
        else:
            self.add_row(tipe, data)

    def add_row(self, tipe, data):
        item = QTreeWidgetItem(self)
        if data is None:
            item.setForeground(0, QBrush(self.theme['NullColor']))
            item.setText(0, 'null')
            return

        if tipe['type'] == 'record':
            row = [(data[att['idn']], att['type']) for att in tipe['atts']]
        else:
            row = [(str(data), tipe)]

        for n, v in enumerate(row):
            value = v[0]
            tipe = v[1]
            if value is None:
                brush = QBrush(self.theme['NullColor'])
                value = 'null'
            else:
                brush = get_type_brush(tipe, self.theme)

            item.setForeground(n, brush)
            item.setText(n, str(value))

    def get_header(self, tipe):
        if tipe['type'] == 'collection':
            return self.get_header(tipe['inner'])
        elif tipe['type'] == 'record':
            return [att['idn'] for att in tipe['atts']]
        else:
            return [tipe['type']]


class QueryTreeView(QWidget):
    def __init__(self, tipe, data, theme=None, parent=None):
        super(QueryTreeView, self).__init__(parent)

        if theme:
            self.theme = theme
        else:
            self.theme = default_theme
        layout = QVBoxLayout()
        self.setLayout(layout)

        font = QFont()
        font.setPointSize(14)
        self.setFont(font)

        toolbar = QToolBar("tree buttons")
        toolbar.setIconSize(QSize(24, 24))
        self.tree = QTreeWidget(self)
        layout.addWidget(toolbar)
        layout.addWidget(self.tree)

        expand_all = QAction(QIcon(os.path.join('images', 'expand.png')), "expand all", self)
        expand_all.setStatusTip("expand all")
        expand_all.triggered.connect(self.tree.expandAll)
        toolbar.addAction(expand_all)

        collapse_all = QAction(QIcon(os.path.join('images', 'collapse.png')), "collapse all", self)
        collapse_all.setStatusTip("collapse all")
        collapse_all.triggered.connect(self.tree.collapseAll)
        toolbar.addAction(collapse_all)

        self.tree.setAlternatingRowColors(True)

        self.tree.setHeaderLabels([tipe['type'], ''])
        if tipe['type'] in ['record', 'collection', 'array'] and data is not None:
            root = self.tree
        else:
            root = QTreeWidgetItem(self.tree)

        self.add_items(root, tipe, data)
        self.tree.expandAll()
        self.tree.setColumnWidth(0, self.width() / 2)

    def add_items(self, root, tipe, data):
        if data is None:
            root.setForeground(1, QBrush(self.theme['NullColor']))
            root.setText(1, 'null')
        elif tipe['type'] == 'record':
            for att in tipe['atts']:
                item = QTreeWidgetItem(root, [att['idn'], att['type']['type']])
                item.setForeground(0, QBrush(self.theme['RecordFieldColor']))
                item.setForeground(1, QBrush(self.theme['RecordInnerColor']))
                self.add_items(item, att['type'], data[att['idn']])

        elif tipe['type'] == 'collection':
            inner = tipe['inner']
            for n, obj in enumerate(data):
                item = QTreeWidgetItem(root, ['[%d]' % n, inner['type']])
                item.setForeground(0, QBrush(self.theme['CollectionIndexColor']))
                item.setForeground(1, QBrush(self.theme['CollectionInnerColor']))
                self.add_items(item, inner, obj)
        else:
            brush = get_type_brush(tipe, self.theme)
            root.setForeground(1, brush)
            root.setText(1, str(data))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    data = [
        dict(a=1, b=dict(d=[1, 2, 3], e="Hello")),
        dict(a=2, b=dict(d=[1, 2, 3], e="world")),
        dict(a=3, b=dict(d=[1, 2, 3], e="again")),
    ]
    tipe = {
        'type': 'collection',
        'inner': {
            'type': 'record',
            'atts': [
                {'idn': 'a', 'type': {'type': 'int'}},
                {'idn': 'b', 'type': {'type': 'record', 'atts': [
                    {'idn': 'd', 'type': {'type': 'collection', 'inner': {'type': 'int'}}},
                    {'idn': 'e', 'type': {'type': 'string'}}
                ]}}
            ]
        }
    }
    ex1 = QueryView()
    ex1.show_data(tipe, data)
    ex1.show()

    sys.exit(app.exec_())
    app = QtGui.QApplication(sys.argv)
