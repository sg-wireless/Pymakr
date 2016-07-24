#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#
# This is the install script for the eric6 debug client. It may be used
# to just install the debug clients for remote debugging.
#

"""
Installation script for the eric6 debug clients.
"""

from __future__ import unicode_literals, print_function
try:
    import cStringIO as io
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    sip.setapi('QTextStream', 2)
except (ImportError):
    import io    # __IGNORE_WARNING__

import sys
import os
import re
import compileall
import shutil
import fnmatch
import distutils.sysconfig

# Define the globals.
progName = None
currDir = os.getcwd()
modDir = None
pyModDir = None
distDir = None
installPackage = "eric6DebugClients"
doCleanup = True
doCompile = True
sourceDir = "eric"


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

    @param rcode the return code passed back to the calling process.
    """
    global progName, modDir, distDir

    print()
    print("Usage:")
    if sys.platform == "darwin":
        print("    {0} [-chz] [-d dir] [-i dir]".format(progName))
    elif sys.platform.startswith("win"):
        print("    {0} [-chz] [-d dir]".format(progName))
    else:
        print("    {0} [-chz][-d dir] [-i dir]".format(progName))
    print("where:")
    print("    -h, --help display this help message")
    print("    -d dir     where eric6 debug client files will be installed")
    print("               (default: {0})".format(modDir))
    if not sys.platform.startswith("win"):
        print("    -i dir     temporary install prefix")
        print("               (default: {0})".format(distDir))
    print("    -c         don't cleanup old installation first")
    print("    -z         don't compile the installed python files")

    exit(rcode)


def initGlobals():
    """
    Module function to set the values of globals that need more than a
    simple assignment.
    """
    global modDir, pyModDir

    modDir = distutils.sysconfig.get_python_lib(True)
    pyModDir = modDir


def copyTree(src, dst, filters, excludeDirs=[], excludePatterns=[]):
    """
    Copy files of a directory tree.
    
    @param src name of the source directory
    @param dst name of the destination directory
    @param filters list of filter pattern determining the files to be copied
    @param excludeDirs list of (sub)directories to exclude from copying
    @keyparam excludePatterns list of filter pattern determining the files to
        be skipped
    """
    try:
        names = os.listdir(src)
    except OSError:
        # ignore missing directories
        return
    
    for name in names:
        skipIt = False
        for excludePattern in excludePatterns:
            if fnmatch.fnmatch(name, excludePattern):
                skipIt = True
                break
        if not skipIt:
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            for filter in filters:
                if fnmatch.fnmatch(srcname, filter):
                    if not os.path.isdir(dst):
                        os.makedirs(dst)
                    shutil.copy2(srcname, dstname)
                    os.chmod(dstname, 0o644)
                    break
            else:
                if os.path.isdir(srcname) and srcname not in excludeDirs:
                    copyTree(srcname, dstname, filters,
                             excludePatterns=excludePatterns)


def cleanupSource(dirName):
    """
    Cleanup the sources directory to get rid of leftover files
    and directories.
    
    @param dirName name of the directory to prune (string)
    """
    # step 1: delete the __pycache__ directory and all *.pyc files
    if os.path.exists(os.path.join(dirName, "__pycache__")):
        shutil.rmtree(os.path.join(dirName, "__pycache__"))
    for name in [f for f in os.listdir(dirName)
                 if fnmatch.fnmatch(f, "*.pyc")]:
        os.remove(os.path.join(dirName, name))
    
    # step 2: descent into subdirectories and delete them if empty
    for name in os.listdir(dirName):
        name = os.path.join(dirName, name)
        if os.path.isdir(name):
            cleanupSource(name)
            if len(os.listdir(name)) == 0:
                os.rmdir(name)


def cleanUp():
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
            'Error: {0}\nTry install with admin rights.\n'.format(msg))
        exit(7)


def shutilCopy(src, dst, perm=0o644):
    """
    Wrapper function around shutil.copy() to ensure the permissions.
    
    @param src source file name (string)
    @param dst destination file name or directory name (string)
    @keyparam perm permissions to be set (integer)
    """
    shutil.copy(src, dst)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    os.chmod(dst, perm)


def installEricDebugClients():
    """
    Actually perform the installation steps.
    
    @return result code (integer)
    """
    global distDir, doCleanup, sourceDir, modDir
    
    # set install prefix, if not None
    if distDir:
        targetDir = os.path.normpath(os.path.join(distDir, installPackage))
    else:
        targetDir = os.path.join(modDir, installPackage)
    
    try:
        # Install the files
        # copy the various parts of eric6 debug clients
        copyTree(
            os.path.join(sourceDir, "DebugClients"), targetDir,
            ['*.py', '*.pyc', '*.pyo', '*.pyw'],
            ['{1}{0}.ropeproject'.format(os.sep, sourceDir)],
            excludePatterns=["eric6config.py*"])
        copyTree(
            os.path.join(sourceDir, "DebugClients"), targetDir,
            ['*.rb'],
            ['{1}{0}Examples'.format(os.sep, sourceDir)])
        
        # copy the license file
        shutilCopy(
            '{1}{0}LICENSE.GPL3'.format(os.sep, sourceDir), targetDir)
        
    except (IOError, OSError) as msg:
        sys.stderr.write(
            'Error: {0}\nTry install with admin rights.\n'.format(msg))
        return(7)
    
    return 0


def main(argv):
    """
    The main function of the script.

    @param argv the list of command line arguments.
    """
    import getopt

    # Parse the command line.
    global progName, modDir, doCleanup, doCompile, distDir
    global sourceDir
    
    if sys.version_info < (2, 7, 0) or sys.version_info > (3, 9, 9):
        print('Sorry, eric6 requires at least Python 2.7 or '
              'Python 3 for running.')
        exit(5)
    
    progName = os.path.basename(argv[0])
    
    if os.path.dirname(argv[0]):
        os.chdir(os.path.dirname(argv[0]))
    
    initGlobals()

    try:
        if sys.platform.startswith("win"):
            optlist, args = getopt.getopt(
                argv[1:], "chzd:", ["help"])
        elif sys.platform == "darwin":
            optlist, args = getopt.getopt(
                argv[1:], "chzd:i:", ["help"])
        else:
            optlist, args = getopt.getopt(
                argv[1:], "chzd:i:", ["help"])
    except getopt.GetoptError as err:
        print(err)
        usage()

    for opt, arg in optlist:
        if opt in ["-h", "--help"]:
            usage(0)
        elif opt == "-d":
            modDir = arg
        elif opt == "-i":
            distDir = os.path.normpath(arg)
        elif opt == "-c":
            doCleanup = False
        elif opt == "-z":
            doCompile = False
    
    installFromSource = not os.path.isdir(sourceDir)
    if installFromSource:
        sourceDir = os.path.dirname(__file__) or "."
    
    # cleanup source if installing from source
    if installFromSource:
        print("Cleaning up source ...")
        cleanupSource(os.path.join(sourceDir, "DebugClients"))
        print()
    
    # cleanup old installation
    try:
        if doCleanup:
            print("Cleaning up old installation ...")
            if distDir:
                shutil.rmtree(distDir, True)
            else:
                cleanUp()
    except (IOError, OSError) as msg:
        sys.stderr.write('Error: {0}\nTry install as root.\n'.format(msg))
        exit(7)

    if doCompile:
        print("\nCompiling source files ...")
        if sys.version_info[0] == 3:
            skipRe = re.compile(r"DebugClients[\\/]Python[\\/]")
        else:
            skipRe = re.compile(r"DebugClients[\\/]Python3[\\/]")
        # Hide compile errors (mainly because of Py2/Py3 differences)
        sys.stdout = io.StringIO()
        if distDir:
            compileall.compile_dir(
                os.path.join(sourceDir, "DebugClients"),
                ddir=os.path.join(distDir, modDir, installPackage),
                rx=skipRe,
                quiet=True)
        else:
            compileall.compile_dir(
                os.path.join(sourceDir, "DebugClients"),
                ddir=os.path.join(modDir, installPackage),
                rx=skipRe,
                quiet=True)
        sys.stdout = sys.__stdout__
    print("\nInstalling eric6 debug clients ...")
    res = installEricDebugClients()
    
    print("\nInstallation complete.")
    print()
    
    exit(res)
    
    
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
