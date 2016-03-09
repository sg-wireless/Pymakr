========================
README for the eric6 IDE
========================

1. Installation
---------------
Installing eric6 is a simple process. Just execute the ``install.py`` script
(type ``python install.py -h`` for some help). Please note that the
installation has to be performed using the administrators account (i.e. root
on linux). This installs a wrapper script called eric6 in the standard
executable directory.

If you want to uninstall the package just execute the ``uninstall.py`` script.
This gets rid of all installed files. In this case please send an email to the
below mentioned address and tell me your reason. This might give me a hint on
how to improve eric6.

eric6 may be used with any combination of Python 3 or 2, Qt5 or Qt4 and
PyQt5 or PyQt4. If the required packages (Qt5/4, QScintilla2, sip and PyQt5/4)
are not installed, please get them and install them in the following order
(order is important).

1. Install Qt5 (from The Qt Company)

2. Build and install QScintilla2 (from Riverbank Computing)

3. Build and install sip (from Riverbank Computing)

4. Build and install PyQt5 (from Riverbank Computing)

5. Build and install QScintilla2 Python bindings
   (part of the QScintilla2 package)

6. Install eric6

If you want to use the interfaces to other supported software packages, you may
install them in any order and at any time.

Please note, that the QScintilla2 Python bindings have to be rebuild, if
the PyQt5 package gets updated. If this step is omitted, a bunch of strange
errors will occur.

1.1 Installation on Windows®
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Installing eric6 on Windows® is even easier. Just download the PyQt5
installer from Riverbank Computing and use it to install PyQt5. This includes
all the required Qt5 libraries and tools as well as QScintilla. Once
this installation is completed install eric6. That's all.

2. Installation of translations
-------------------------------
Translations of the eric6 IDE are available as separate downloads. There
are two ways to install them.

The first possibility is to install them together with eric6. In order
to do that, simply extract the downloaded archives into the same place
as the eric6 archive and follow the installation instructions above.

The second possibility is to install them separately. Extract the
downloaded archives and execute the install-i18n.py script (type
``python install-i18n.py -h`` for some help). This way you can make the
translations available to everybody or just to the user executing the
installation command (if using the -p switch).

3. Running
----------
Just call up eric6, which will start the IDE. Use the "what is"-help
(arrow with ?) to get some help. The eric web site provides some
documents describing certain aspects of eric. To start the unit test module in
a standalone variant simply call up eric6_unittest. This will show the same
dialog (though with a little bit less functionality) as if started from within
eric6. The web browser can be started as a standalone program by executing the
pymakr_webbrowser script.

Please note, the first time you start eric6 it will recognize, that it
hasn't been configured yet and will show the configuration dialog.
Please take your time and go through all the configuration items.
However, every configuration option has a meaningful default value.

4. Running from the sources
---------------------------
If you want to run eric6 from within the source tree you have to execute
the ``compileUiFiles.py`` script once after a fresh checkout from the source
repository or when new dialogs have been added. Thereafter just execute
the ``pymakr.py`` script.

5. Tray starter
---------------
eric6 comes with a little utility called "eric6_tray". This embeds an icon
in the system tray, which contains a context menu to start eric6 and all
it's utilities. Double clicking this icon starts the eric6 IDE.

6. Autocompletion/Calltips
--------------------------
eric6 provides an interface to the QScintilla auto-completion and calltips
functionality. QScintilla2 comes with API files for Python and itself. PyQt4
and PyQt5 contain API files as well. These are installed by default, if the
correct installation order (see above) is followed. An API file for eric6 is
installed in the same place.

In order to use autocompletion and calltips in eric6 please configure these
functions in the "Preferences Dialog" on the "Editor -> APIs", 
"Editor -> Autocompletion" and "Editor -> Calltips" pages.

7. Remote Debugger
------------------
In order to enable the remote debugger start eric6, open the preferences
dialog and configure the settings on the debugger pages.

The remote login must be possible without any further interaction (i.e.
no password prompt). If the remote setup differs from the local one you
must configure the Python interpreter and the Debug Client to be used
in the Preferences dialog. eric6 includes two different versions of the
debug client. ``DebugClient.py`` is the traditional debugger and
``DebugClientThreads.py`` is a multithreading variant of the debug client.
Please copy all needed files to a place accessible through the Python path
of the remote machine and set the entries of the a.m. configuration tab
accordingly. 

8. Passive Debugging
--------------------
Passive debugging mode allows the startup of the debugger from outside
of the IDE. The IDE waits for a connection attempt. For further details
see the file README-passive-debugging.rst.

9. Plug-in System
-----------------
eric6 contains a plug-in system, that is used to extend eric6's 
functionality. Some plug-ins are part of eric6. Additional plugins
are available via the Internet. Please use the built-in plug-in
repository dialog to get a list of available (official) plug-ins
and to download them. For more details about the plug-in system
please see the documentation area.

10. Interfaces to additional software packages
----------------------------------------------
At the moment eric6 provides interfaces to the following software
packages.

    Qt-Designer 
        This is part of the Qt distribution and is used to generate user
        interfaces.
    
    Qt-Linguist 
        This is part of the Qt distribution and is used to generate
        translations.
    
    Qt-Assistant 
        This is part of the Qt distribution and may be used to display help
        files.
    
    Mercurial
        This is a distributed version control system available from
        <http://mercurial.selenic.com>. It is the one used by eric6 itself.
    
    Subversion 
        This is a version control system available from
        <http://subversion.apache.org>. eric6 supports two different Subversion
        interfaces. One is using the svn command line tool, the other is using
        the PySvn Python interface <pysvn.tigris.org>. The selection is done
        automatically depending on the installed software. The PySvn interface
        is prefered. This automatism can be overridden an a per project basis
        using the "User Properties" dialog.
    
    coverage.py 
        This is a tool to check Python code coverage. A slightly modified
        version is part of the eric6 distribution. The original version is
        available from <http://www.nedbatchelder.com/code/modules/coverage.html>
    
    tabnanny 
        This is a tool to check Python code for white-space related problems.
        It is part of the standard Python installation.
    
    profile 
        This is part of the standard Python distribution and is used to profile
        Python source code.

11. Internationalization
------------------------
eric6 and its tools are prepared to show the UI in different languages, which
can be configured via the preferences dialog. The Qt and QScintilla
translations are searched in the translations directory given in the
preferences dialog (Qt page). If the translations cannot be found, some part
of the MMI might show English texts even if you have selected something else.
If you are missing eric6 translations for your language and are willing to
volunteer for this work please send me an email naming the country code and
I will send you the respective Qt-Linguist file.

12. Window Layout
-----------------
eric6 provides different window layouts. In these layouts, the shell window
and the file browser may be embedded or be separat windows.

13. Source code documentation
-----------------------------
eric6 has a built in source code documentation generator, which is
usable via the commandline as well. For further details please see
the file README-eric6-doc.rst.

14. License
-----------
eric6 (and the others) is released under the conditions of the GPL. See 
separate license file for more details. Third party software included in
eric6 is released under their respective license and contained in the
eric6 distribution for convenience. 

15. Bugs and other reports
--------------------------
Please send bug reports, feature requests or contributions to eric bugs
address. After the IDE is installed you can use the "Report Bug..."
entry of the Help menu, which will send an email to
<eric-bugs@eric-ide.python-projects.org. To request a new feature use the
"Request Feature..." entry of the Help menu, which will send an email to
<eric-featurerequest@eric-ide.python-projects.org.
