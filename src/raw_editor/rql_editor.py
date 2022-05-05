from theme import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qsci import QsciScintilla, QsciLexerCustom, QsciAPIs

import sys
import re
from multiprocessing import Process
from time import sleep

default_theme = {
    "DefaultFont": QFont("Consolas", 12),
    "DefaultColor": QColor("#FF000000"),
    "DefaultPaperColor": QColor("#FFFFFFFF"),
    'MarginBackGroundColor': QColor('#cccccc'),
    'MarkerBackgroundColor': QColor("#ee1111"),
    'CaretForegroundColor': [],
    'CaretLineBackgroundColor': QColor("#ffe4e4"),
    'MatchedBraceForegroundColor': QColor("#ff0000"),
    'MatchedBraceBackgroundColor': QColor("#ffffff"),
    "styles": {
        'default': {'color': QColor('#000000'), 'bold': False},
        'keywords': {'color': QColor('#00007f'), 'bold': True},
        'constants': {'color': QColor('#007f7f'), 'bold': True},
        'comments': {'color': QColor('#7f7f7f'), 'bold': False},
        'strings': {'color': QColor('#cc6600'), 'bold': False},
        'builtInFunctions': {'color': QColor('#007f00'), 'bold': True},
        'operators': {'color': QColor('#9f5000'), 'bold': False},
        'parens': {'color': QColor('#000000'), 'bold': True},
        'numbers': {'color': QColor('#7f007f'), 'bold': False},
    }
}


class RawLexer(QsciLexerCustom):

    def __init__(self, theme=default_theme, parent=None):
        super(RawLexer, self).__init__(parent)

        # Default text settings
        # ----------------------
        self.setDefaultColor(theme["DefaultColor"])
        self.setDefaultPaper(theme["DefaultPaperColor"])
        self.setDefaultFont(theme["DefaultFont"])

        # Initialize colors per style
        # ----------------------------
        self.styles = dict()
        self.style_names = dict()
        self.regexes = []
        # self.theme = theme

        for name, value in theme['styles'].items():
            self.add_style(name, value['color'], bold=value['bold'])

        self.keywords = ['select', 'distinct', 'from', 'where', 'group', 'by', 'having', 'in',
                         'union', 'order', 'desc', 'asc', 'if', 'then', 'else', 'parse',
                         'parse?', 'into', 'not', 'and', 'or', 'flatten', 'like', 'as',
                         'all', 'cast', 'partition', 'on', 'error', 'fail', 'skip',
                         'when', 'coalesce', 'enumerate']

        self.builtin_functions = ['avg', 'count', 'exists', 'max', 'min', 'sum', 'trim', 'startswith',
                                  'cavg', 'ccount', 'cmax', 'cmin', 'csum', 'isnull', 'isnone',
                                  'date_trunc', 'strempty', 'to_date', 'to_time', 'to_timestamp', 'enumerate',
                                  'read', 'read_many', 'read_csv', 'read_parquet_raw', 'read_parquet_avro', 'read_json',
                                  'read_xml', 'read_pgsql', 'read_mysql', 'read_oracle', 'read_sqlserver', 'read_hive',
                                  'read_sqlite', 'query_pgsql', 'query_mysql', 'query_oracle', 'query_sqlserver',
                                  'try_read', 'try_read_many', 'try_read_csv', 'try_read_json', 'try_read_xml',
                                  'try_read_pgsql', 'try_read_mysql', 'try_read_oracle',
                                  'try_read_sqlserver', 'try_read_hive', 'try_read_sqlite', 'try_query_pgsql',
                                  'try_query_mysql', 'try_query_oracle', 'try_query_sqlserver',
                                  'ls', 'ls_schemas', 'ls_tables']

        self.operators = r':|\+|\-|\/|\/\/|%|<@>|@>|<@|&|\^|~|<|>|<=|=>|==|!=|:=|<>|='

        self.constants = ['typealias', 'true', 'false', 'null', 'none', 'string', 'int',
                          'long', 'short', 'byte', 'float', 'double', 'decimal',
                          'date', 'time', 'timestamp', 'interval', 'bool', 'collection',
                          'array', 'record', 'format', 'auto', 'csv', 'json',
                          'excel', 'hjson', 'xml', 'text', 'nullif']

        self.add_match('keywords', self.keywords)
        self.add_match('builtInFunctions', self.builtin_functions)
        self.add_match('constants', self.constants)
        self.add_match('numbers', r'\b[+-]?\d+(?:(?:\.\d*)?(?:[e][+-]?\d+)?)?\b')
        self.add_match('comments', r'\/\/[^\n]*')
        self.add_match('operators', r':|\+|\-|\/|%|<@>|@>|<@|&|\^|~|<|>|<=|=>|==|!=|:=|<>|=')

        self.add_match('parens', r"[\(\[\{\)\]\}]")
        self.add_match('strings', r'r?"(?:[^"\\]|\\.)*"')

        # when nothing else matches takes the next token
        self.next_token = re.compile(r'^\s+|\w+|\W')
        # multiline string is handled differently
        self.multiline_string = re.compile('^"""')

    def add_match(self, style, obj, case_sensitive=False):
        if isinstance(obj, str):
            regex = obj
        elif isinstance(obj, list):
            regex = r'|'.join([r'\b' + r + r'\b' for r in obj])
        else:
            raise Exception('match can only be a string or a list of keywords')

        # adds the ^ at the beginning to match only at the beginning of the string
        if not case_sensitive:
            r = re.compile("^" + regex, re.IGNORECASE)
        else:
            r = re.compile("^" + regex)
        style_number = self.styles[style]
        self.regexes.append((r, style_number))

    def add_style(self, name, color, paper=None, bold=False):
        count = len(self.styles)
        self.styles[name] = count
        self.style_names[count] = name

        self.setColor(color, count)
        font = self.defaultFont()
        font.setBold(bold)
        self.setFont(font, count)
        if paper:
            self.setPaper(paper, count)

    def language(self):
        return "custom language"

    def description(self, style):
        if style in self.style_names:
            return self.style_names[style]
        else:
            return ""

    def styleText(self, start, end):
        # Called everytime the editors text has changed
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        text = self.parent().text()[start:end]

        # Tries a regex and if it matches applies the style and removes token from text
        def try_match(regex, style):
            nonlocal text
            m = regex.match(text)
            if m:
                token = m.group(0)
                self.setStyling(len(token), style)
                text = text[len(token):]
                return True
            return False

        while text:
            for (regex, style) in self.regexes:
                if try_match(regex, style):
                    continue
            # if noting matches sets the default style (0)
            try_match(self.next_token, 0)


class RqlEditor(QsciScintilla):
    ARROW_MARKER_NUM = 8

    def __init__(self, theme=default_theme, parent=None):
        super(RqlEditor, self).__init__(parent)

        if theme:
            self.theme = theme
        else:
            self.theme = default_theme

        self.setTabWidth(4)
        # Set the default font
        font = self.theme['DefaultFont']
        font.setFixedPitch(True)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width('00000') + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(self.theme['MarginBackGroundColor'])

        self.setMatchedBraceForegroundColor(self.theme['MatchedBraceForegroundColor'])
        self.setUnmatchedBraceForegroundColor(self.theme['MatchedBraceForegroundColor'])
        self.setMatchedBraceBackgroundColor(self.theme['MatchedBraceBackgroundColor'])
        self.setUnmatchedBraceBackgroundColor(self.theme['MatchedBraceBackgroundColor'])

        # self.setMatchedBraceIndicator(1)
        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        #        self.connect(self,
        #            SIGNAL('marginClicked(int, int, Qt::KeyboardModifiers)'),
        #            self.on_margin_clicked)
        self.markerDefine(QsciScintilla.RightArrow,
                          self.ARROW_MARKER_NUM)
        self.setMarkerBackgroundColor(self.theme['MarkerBackgroundColor'],
                                      self.ARROW_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(self.theme['CaretLineBackgroundColor'])
        if 'CaretForegroundColor' in theme:
            self.setCaretForegroundColor(self.theme['CaretForegroundColor'])

        # Lexer for syntax highlighting
        self.lexer = RawLexer(theme=self.theme, parent=self)
        self.setLexer(self.lexer)

        self.setAutoCompletionThreshold(3)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)

        # Create new api for auto-complete
        self.api = QsciAPIs(self.lexer)
        # adds all keywords
        for s in self.lexer.keywords + self.lexer.constants + self.lexer.builtin_functions:
            self.api.add(s)

        self.api.prepare()
        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        # not too small
        self.setMinimumSize(600, 450)

        # thread to start stop the the undo collection (will save each 5 seconds)
        self.undo_thread = Process(name='Undo thread', target=self.undo_loop, daemon=True)
        self.undo_thread.start()

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.ARROW_MARKER_NUM)
        else:
            self.markerAdd(nline, self.ARROW_MARKER_NUM)

    # To keep compatibility with the main window
    def selectAll(self):
        super().selectAll(True)

    def undo_loop(self):
        while True:
            self.beginUndoAction()
            sleep(2)
            self.endUndoAction()

    def stop(self):
        self.undo_thread.terminate()

    # Some how disabling the editor makes it loose the margin color
    def setEnabled(self, bool):
        super().setEnabled(bool)
        self.setMarginsBackgroundColor(self.theme["MarginBackGroundColor"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # opening default theme
    with open('conf.json') as f:
        conf = json.load(f)
    theme = load_theme(conf['theme'])
    palette = QPalette()
    for name, value in theme["Widgets"].items():
        palette.setColor(QPalette.__dict__[name], value)
    app.setPalette(palette)

    editor = RqlEditor(theme['Editor'])
    editor.show()
    text = r'''
typealias person := record(name: string, age: int, salary: double);    
a := select * from read("dropbox://cesar/test");    
b := "\"hello\" \"world\"";
c := 123.3e23 + 2 < 45;
d := null;
ccount(a)'''
    editor.setText(text)
    app.exec_()
