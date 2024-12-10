#!/bin/bash

python3 setup.py bdist_wheel
pip3 install ${@} dist/ofReader-0.2.2-py3-none-any.whl
