#!/usr/bin/env bash
pyi-makespec --paths=src/raw_editor src/raw_editor/main_window.py --name raw-editor --hidden-import PyQt5.QtPrintSupport -w --onefile 
pyinstaller raw-editor.spec
