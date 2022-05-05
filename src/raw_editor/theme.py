from PyQt5.QtGui import *
import json


def load_theme(filename):
    def object_hook(obj):
        if '__type__' in obj:
            if obj['__type__'] == 'color':
                return QColor(obj['color'])
            elif obj['__type__'] == 'font':
                return QFont(obj['family'], obj['pointSize'])
            else:
                raise Exception('unknown object type ', obj['__type__'])
        else:
            return obj

    print('filename', filename)
    with open(filename) as f:
        data = json.load(f, object_hook=object_hook)
    return data


def save_theme(filename, data):
    def default(obj):
        if isinstance(obj, QColor):
            color = hex(obj.rgb())
            return dict(__type__="color", color=color.replace("0x", "#"))
        elif isinstance(obj, QFont):
            QFont()
            return dict(__type__="font", pointSize=obj.pointSize(), family=obj.family())

    with open(filename, "w") as f:
        json.dump(data, f, default=default, indent=2)
