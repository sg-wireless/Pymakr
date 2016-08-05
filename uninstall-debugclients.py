#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the uninstall script for the eric6 debug client.
#

"""
Unnstallation script for the eric6 debug clients.
"""

from __future__ import unicode_literals, print_function

import sys
import os
import shutil
import distutils.sysconfig

if sys.version_info[0] == 2:
    import sip
    sip.setapi('QString', 2)

# Define the globals.
progName = None
currDir = os.getcwd()
modDir = None
pyModDir = None
installPackage = "eric6DebugClients"


def exit(rcode=0):
    """
    Exit the install script.
    
    @param rcode result code to report back (integer)
    """
    global currDir
    
    if sys.platform.startswith("win"):
        # different meaning of input between Py2 and Py3
        try:
            input("Press enter to continue...")
        except (EOFError, SyntaxError):
            pass
    
    os.chdir(currDir)
    
    sys.exit(rcode)


def usage(rcode=2):
    """
    Display a usage message and exit.

    @param rcode return code passed back to the calling process (integer)
    """
    global progName

    print("Usage:")
    print("    {0} [-h]".format(progName))
    print("where:")
    print("    -h             display this help message")

    exit(rcode)


def initGlobals():
    """
    Module function to set the values of globals that need more than a
    simple assignment.
    """
    global modDir, pyModDir

    modDir = distutils.sysconfig.get_python_lib(True)
    pyModDir = modDir


def uninstallEricDebugClients():
    """
    Uninstall the old eric debug client files.
    """
    global pyModDir
    
    try:
        # Cleanup the install directories
        dirname = os.path.join(pyModDir, installPackage)
        if os.path.exists(dirname):
            shutil.rmtree(dirname, True)
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry uninstall with admin rights.\n'.format(msg))
        exit(7)


def main(argv):
    """
    The main function of the script.

    @param argv the list of command line arguments.
    """
    import getopt

    initGlobals()

    # Parse the command line.
    global progName
    progName = os.path.basename(argv[0])
    
    try:
        optlist, args = getopt.getopt(argv[1:], "hy")
    except getopt.GetoptError:
        usage()

    for opt, arg in optlist:
        if opt in ["-h", "--help"]:
            usage(0)
    
    print("\nUninstalling eric6 debug clients ...")
    uninstallEricDebugClients()
    print("\nUninstallation complete.")
    print()
    
    exit(0)
    
    
if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except Exception:
        print("""An internal error occured.  Please report all the output"""
              """ of the program,\nincluding the following traceback, to"""
              """ eric-bugs@eric-ide.python-projects.org.\n""")
        raise

#
# eflag: noqa = M801
