#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Script for eric6 to compile all .ui files to Python source.
"""

from __future__ import unicode_literals
from __future__ import print_function

import sys

# step 1: determine PyQt variant, preferring PyQt5
try:
    import PyQt5        # __IGNORE_WARNING__
    pyqtVariant = "PyQt5"
except ImportError:
    import PyQt4    # __IGNORE_WARNING__
    pyqtVariant = "PyQt4"

# step 2: compile the UI files
if pyqtVariant == "PyQt4":
    from PyQt4.uic import compileUiDir
else:
    from PyQt5.uic import compileUiDir


def __pyName(py_dir, py_file):
    """
    Local function to create the Python source file name for the compiled
    .ui file.
    
    @param py_dir suggested name of the directory (string)
    @param py_file suggested name for the compile source file (string)
    @return tuple of directory name (string) and source file name (string)
    """
    return py_dir, "Ui_{0}".format(py_file)


def compileUiFiles():
    """
    Compile the .ui files to Python sources.
    """
    compileUiDir(".", True, __pyName)


def main(argv):
    """
    The main function of the script.

    @param argv the list of command line arguments.
    """
    # Compile .ui files
    print("Compiling user interface files...")
    compileUiFiles()
    
    
if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except:
        print(
            "\nAn internal error occured.  Please report all the output of the"
            " program, \nincluding the following traceback, to"
            " eric-bugs@eric-ide.python-projects.org.\n")
        raise
