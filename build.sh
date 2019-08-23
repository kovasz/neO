#!/bin/bash

pyinstaller --onefile --add-binary '/usr/local/lib64/python3.6/site-packages/z3/lib/libz3.so:.' --hidden-import="numpy.random.common" --hidden-import="numpy.random.bounded_integers" --hidden-import="numpy.random.entropy" networkOptimizer.py
