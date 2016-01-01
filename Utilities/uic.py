# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a function to compile all user interface files of a
directory or directory tree.
"""

from __future__ import unicode_literals

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


def compileUiFiles(dir, recurse=False):
    """
    Module function to compile the .ui files of a directory tree to Python
    sources.
    
    @param dir name of a directory to scan for .ui files (string)
    @param recurse flag indicating to recurse into subdirectories (boolean)
    """
    compileUiDir(dir, recurse, __pyName)
