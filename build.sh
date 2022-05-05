#!/bin/bash -exu
SCRIPT_HOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${SCRIPT_HOME}"
rm -rf dist
python3 setup.py clean sdist bdist_wheel
