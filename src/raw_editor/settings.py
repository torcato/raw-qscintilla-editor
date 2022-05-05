from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

from rawapi import new_raw_client, RawException


def text_or_none(s):
    return s if s else None


def exception_dialog(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RawException as e:
            print('RawException', e)
            error_box(str(e))
        except Exception as e:
            print('Exception', e)
            error_box("Unexpected Error", e)

    return wrapper


def error_box(msg, exception=None):
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle("Error")
    box.setText(msg)
    if exception:
        box.setDetailedText(str(exception))
    box.setStandardButtons(QMessageBox.Close)
    return box.exec_()


class RegisterDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.widgets = dict()
        self.labels = dict()
        self.gridLayout = QGridLayout(self)
        for n, data in enumerate(settings):
            widget = self.new_widget(data)
            label = QLabel(data['label'])
            self.gridLayout.addWidget(label, n, 0, 1, 1)
            self.gridLayout.addWidget(widget, n, 1, 1, 2)
            self.widgets[data['name']] = widget
            self.labels[data['name']] = label

        self.ok_btn = QPushButton('ok')
        self.ok_btn.clicked.connect(self.register)
        self.cancel_btn = QPushButton('cancel')
        self.cancel_btn.clicked.connect(self.reject)

        self.gridLayout.addWidget(self.ok_btn, n + 1, 1, 1, 1)
        self.gridLayout.addWidget(self.cancel_btn, n + 1, 2, 1, 1)
        self.registered = False

    def hide_widget(self, name):
        self.widgets[name].hide()
        self.labels[name].hide()

    def show_widget(self, name):
        self.widgets[name].show()
        self.labels[name].show()

    def new_widget(self, data):
        if data['type'] == 'text':
            widget = QLineEdit(self)
        elif data['type'] == 'password':
            widget = QLineEdit(self)
            widget.setEchoMode(QLineEdit.Password)
        elif  data['type'] == 'multiline-text':
            widget = QPlainTextEdit(self)
        elif data['type'] == 'selection':
            widget = QComboBox(self)
            widget.addItems(data['items'])
        else:
            raise Exception('Unknow widget type %s' % type)
        return widget

    def exec_(self):
        super().exec_()
        return self.registered

    # The signal for buttons (clicked) has a state variable
    # It needs to be here when using decorators (for error handling?) or it would throw
    def register(self, state):
        raise NotImplementedError()


class CredentialsListWindow(QDialog):
    def __init__(self, title, fields):
        super().__init__()
        self.setWindowTitle(title)
        self.client = new_raw_client()
        self.fields = fields
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setGeometry(300, 300, 400, 300)
        self.register_btn = QPushButton('Register New')
        self.register_btn.clicked.connect(self.register)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.register_btn)
        vbox = QVBoxLayout()
        vbox.addWidget(self.table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.refresh()

    @exception_dialog
    def refresh(self):
        data = self.get_rows()
        self.table.clear()
        if data:
            nfields = len(self.fields)
            self.table.setColumnCount(nfields + 1)
            self.table.setHorizontalHeaderLabels([''] + self.fields)
            header = self.table.horizontalHeader()
            self.table.setColumnWidth(0, 40)
            for n in range(nfields):
                header.setSectionResizeMode(n + 1, QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
            self.table.setAlternatingRowColors(True)
            self.table.setRowCount(len(data))
            for n, row in enumerate(data):
                button = QPushButton('')
                button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TrashIcon')))
                button.clicked.connect(lambda *args, name=row[0]: self.unregister(name))
                self.table.setCellWidget(n, 0, button)
                for i, value in enumerate(row):
                    self.table.setItem(n, i + 1, QTableWidgetItem(value))
        else:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels([''])
            header = self.table.horizontalHeader()
            header.setStretchLastSection(True)
            self.table.setItem(0, 0, QTableWidgetItem("Nothing registered"))

    def unregister(self, name):
        raise NotImplementedError()

    def register(self):
        raise NotImplementedError()

    def get_rows(self):
        raise NotImplementedError()


class AddBucketDialog(RegisterDialog):
    def __init__(self, client):
        super().__init__(
            [dict(name='name', type='text', label='Name'),
             dict(name='region', type='selection', label='Region',
                  items=['eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'us-east-2', 'us-east-1', 'us-west-1',
                         'us-west-2', 'ap-east-1', 'ap-south-1', 'ap-northeast-3', 'ap-northeast-2', 'ap-southeast-1',
                         'ap-southeast-2', 'ap-northeast-1', 'ca-central-1', 'cn-north-1', 'cn-northwest-1',
                         'eu-central-1', 'sa-east-1']),
             dict(name='access key', type='text', label='Access Key'),
             dict(name='private key', type='text', label='Private Key')])
        self.setWindowTitle("Register S3 Bucket")
        self.client = client

    @exception_dialog
    def register(self, state):
        name = self.widgets['name'].text()
        region = self.widgets['region'].currentText()
        access_key = self.widgets['access key'].text()
        private_key = self.widgets['private key'].text()

        if not name:
            error_box("name has to be defined")
            return

        self.client.buckets_register(name, region, text_or_none(access_key), text_or_none(private_key))
        self.registered = True
        self.accept()


class S3SettingsWindow(CredentialsListWindow):

    def __init__(self):
        super().__init__("S3 Buckets", ['name', 'region', 'credentials'])

    @exception_dialog
    def unregister(self, name):
        self.client.buckets_unregister(name)
        self.refresh()

    def register(self):
        dialog = AddBucketDialog(self.client)
        value = dialog.exec_()
        if value:
            self.refresh()

    def get_rows(self):
        values = []
        for name in self.client.buckets_list():
            b = self.client.buckets_show(name)
            creds = b['credentials'] is not None
            values.append([b['name'], b['region'], str(creds)])
        return values


class RdbmsSettingsWindow(CredentialsListWindow):
    def __init__(self):
        super().__init__("RDBMS Servers", ['name', 'type', 'host', 'database', 'port', 'username'])
        self.setGeometry(300, 300, 500, 300)

    @exception_dialog
    def unregister(self, name):
        self.client.rdbms_unregister(name)
        self.refresh()

    def register(self):
        dialog = AddRdbmsDialog(self.client)
        value = dialog.exec_()
        if value:
            self.refresh()

    def get_rows(self):
        values = []
        for name in self.client.rdbms_list():
            b = self.client.rdbms_show(name)
            database = b['database'] if 'database' in b else '-'
            values.append([name, b['type'], b['host'], database, str(b['port']), b['username']])
        return values


class AddRdbmsDialog(RegisterDialog):
    def __init__(self, client):
        super().__init__(
            [dict(name='name', type='text', label='Name'),
             dict(name='vendor', type='selection', label='Vendor', items=['oracle', 'sqlserver', 'postgres', 'mysql', 'teradata']),
             dict(name='host', type='text', label='host'),
             dict(name='database', type='text', label='Database'),
             dict(name='port', type='text', label='Port'),
             dict(name='username', type='text', label='User Name'),
             dict(name='password', type='password', label='Password'),
            dict(name='extra-options', type='multiline-text', label='Extra Options')]
        )
        self.widgets['port'].setValidator(QIntValidator())
        self.setWindowTitle("Register RDBMS Server")
        self.widgets['vendor'].activated[str].connect(self.vendor_change)
        self.hide_widget('extra-options')
        self.widgets['extra-options'].setMaximumHeight(64)

        self.client = client

    @exception_dialog
    def register(self, state):
        name = self.widgets['name'].text()
        vendor = self.widgets['vendor'].currentText()
        host = self.widgets['host'].text()
        p = self.widgets['port'].text()
        port = int(p) if p else None
        database = self.widgets['database'].text()
        username = text_or_none(self.widgets['username'].text())
        password = text_or_none(self.widgets['password'].text())

        if not name or not host:
            error_box("name and host have to be defined")
            return
        elif vendor in ['postgres', 'mysql', 'sqlserver', 'oracle'] and not database:
            error_box("database has to be defined")
            return

        if vendor == 'postgres':
            self.client.rdbms_register_postgresql(name, host, database, port, username, password)
        elif vendor == 'mysql':
            self.client.rdbms_register_mysql(name, host, database, port, username, password)
        elif vendor == 'sqlserver':
            self.client.rdbms_register_sqlserver(name, host, database, port, username, password)
        elif vendor == 'oracle':
            self.client.rdbms_register_oracle(name, host, database, port, username, password)
        elif vendor == 'teradata':
            options_text = text_or_none(self.widgets['extra-options'].toPlainText())
            opt_list = []
            if options_text:
                def parse_option(l, n):
                    parts = l.split('=')
                    if len(parts) != 2:
                        raise Exception("Error parsing extra-option at line %d" % n)
                    return (parts[0].strip(), parts[1].strip())
                opt_list = [parse_option(l, n) for n, l in enumerate(options_text.split('\n')) if l.strip()]
            self.client.rdbms_register_teradata(name, host, port, username, password, dict(opt_list))
        else:
            raise RawException(
                'Error: Invalid database vendor %s, available options are postgres, mysql, sqlserver, oracle and teradata' % vendor)

        self.registered = True
        self.accept()

    def vendor_change(self, vendor):
        if vendor == 'teradata':
            self.hide_widget('database')
            self.show_widget('extra-options')
        else:
            self.show_widget('database')
            self.hide_widget('extra-options')

class AddHttpAuthDialog(RegisterDialog):
    def __init__(self, client):
        super().__init__(
            [dict(name='name', type='text', label='Url'),
             dict(name='type', type='selection', label='Auth type',
                  items=['oauth-token', 'oauth-client/secret', 'basic-auth']),
             dict(name='token', type='text', label='OAuth Token'),
             dict(name='token-service', type='text', label='Token Service'),
             dict(name='client-id', type='text', label='Client Id'),
             dict(name='client-secret', type='text', label='Client secret'),
             dict(name='refresh-token', type='text', label='Refresh Token'),
             dict(name='use-basic-auth', type='selection', label='Use Basic Auth', items=['false', 'true']),
             dict(name='username', type='text', label='User Name'),
             dict(name='password', type='password', label='Password'),
             ])
        self.setWindowTitle("Register Http Auth")
        self.client = client
        self.widgets['type'].activated[str].connect(self.auth_changed)
        self.auth_changed('oauth-token')

    def auth_changed(self, auth):
        for w in self.widgets:
            self.hide_widget(w)
        self.show_widget('name')
        self.show_widget('type')
        if auth == 'oauth-token':
            self.show_widget('token')
            self.show_widget('refresh-token')
            self.show_widget('token-service')
        elif auth == 'oauth-client/secret':
            self.show_widget('client-id')
            self.show_widget('client-secret')
            self.show_widget('token-service')
            self.show_widget('use-basic-auth')
        elif auth == 'basic-auth':
            self.show_widget('username')
            self.show_widget('password')

    @exception_dialog
    def register(self, state):
        name = self.widgets['name'].text()
        type = self.widgets['type'].currentText()
        if not name:
            error_box("url has to be defined")
            return

        if type == 'oauth-token':
            token = self.widgets['token'].text()
            refreshToken = text_or_none(self.widgets['refresh-token'].text())
            tokenUrl = text_or_none(self.widgets['token-service'].text())
            if not token:
                error_box("token has to be defined")
                return
            credentials = dict(token=token, refreshToken=refreshToken, tokenUrl=tokenUrl)
        elif type == 'oauth-client/secret':
            client_id = self.widgets['client-id'].text()
            client_secret = self.widgets['client-secret'].text()
            oauth_service = self.widgets['token-service'].text()
            useBasicAuth = self.widgets['use-basic-auth'].currentText()
            if not client_id or not client_secret or not oauth_service:
                error_box("client-id, client-secret and token-service have to be defined")
                return
            credentials = dict(clientId=client_id, clientSecret=client_secret, tokenUrl=oauth_service,
                               useBasicAuth=useBasicAuth)
        elif type == 'basic-auth':
            username = self.widgets['username'].text()
            password = self.widgets['password'].text()

            if not username:
                error_box("username has to be defined")
                return
            credentials = dict(user=username, password=password)
        else:
            raise Exception("Unknown auth type: %s" % type)

        self.client.http_auth_register(name, credentials)

        self.registered = True
        self.accept()


class HttpSettingsWindow(CredentialsListWindow):
    def __init__(self):
        super().__init__("Http Auth Urls", ['Url', 'Auth type'])

    @exception_dialog
    def unregister(self, name):
        self.client.http_auth_unregister(name)
        self.refresh()

    def register(self):
        dialog = AddHttpAuthDialog(self.client)
        value = dialog.exec_()
        if value:
            self.refresh()

    def get_rows(self):
        values = []
        for name in self.client.http_auth_list():
            b = self.client.http_auth_show(name)
            values.append([name, b['credentials']['type']])
        return values

class PublishWindow(RegisterDialog):
    def __init__(self, query):
        super().__init__([dict(name='name', type='text', label='Name'),
                         dict(name='publish-as', type='selection', label='Publish As',
                                items=['view', 'materialized view', 'package'])])
        self.setWindowTitle("Publish Query")
        self.client = new_raw_client()
        self.query = query
        self.registered = False

    @exception_dialog
    def register(self, state):
        name = self.widgets['name'].text()
        publish = self.widgets['publish-as'].currentText()
        if not name:
            error_box("name has to be defined")
            return
        if publish == "view":
            self.client.views_create(name, self.query)
        elif publish == "materialized view":
            self.client.materialized_views_create(name, self.query)
        elif publish == "package":
            self.client.packages_create(name, self.query)
        else:
            raise RawException("Unknown publish as %s" % publish)
        self.registered = True
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ex = HttpSettingsWindow()
    # ex.show()
    # ex = S3SettingsWindow()
    # ex.show()
    ex = RdbmsSettingsWindow()
    ex.show()
    # ex = PublishWindow("1+1")
    # ex.show()
    sys.exit(app.exec_())
