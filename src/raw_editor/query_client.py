from PyQt5.QtCore import *

from rawapi import new_raw_client, RawException
import threading
from queue import Queue

class AsyncQueryClient(QObject):

    query_done = pyqtSignal(object, object)
    query_validated = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, parent = None):
        super(AsyncQueryClient, self).__init__(parent)
        self.client = new_raw_client()
        self.run = True
        self.queue = Queue()
        self.thread = threading.Thread(name='Async query', target=self.loop, daemon=True)
        self.thread.start()
        self.executing_cmd = False

    def loop(self):
        while self.run:
            cmd = self.queue.get()
            self.executing_cmd = True
            try:
                if cmd['action'] == 'query':
                    data, tipe = self.client.query(cmd['query'], with_type=True)
                    self.query_done.emit(tipe, data)
                elif cmd['action'] == 'validate':
                    data = self.client.query_validate(cmd['query'])
                    print(data)
                    self.query_validated.emit(data)
                else:
                    raise Exception('Unexpected command %s' % cmd)
            except RawException as e:
                self.error.emit(str(e))
            except ConnectionError as e:
                self.error.emit(str(e))
            except Exception as e:
                print(e)
                raise e
            self.executing_cmd = False

    def query(self, query):
        cmd = dict(action='query', query=query)
        # If the queue does not have slot it will raise an Exception
        self.queue.put(cmd, block=False)

    def validate(self, query):
        cmd = dict(action='validate', query=query)
        # If the queue does not have slot it will raise an Exception
        self.queue.put(cmd, block=False)

    def stop(self):
        self.run = False
