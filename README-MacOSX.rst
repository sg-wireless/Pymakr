====================
Readme for Mac usage
====================

This Readme file describes how to prepare a Mac computer for eric. The
recommended way to do this is to install the software packages from the
distributors web pages. Because some software is only available as source
and compilation is a bit tricky because of the dependencies, these packages
should be installed via a packaging system. The recommended one is MacPorts
because of it's completeness. This is the way described below.


1. Install Xcode
----------------
Open the Mac App Store and enter "xcode" into the search entry at the top
right of the window. From the list of results select the Xcode entry. Xcode
is provided free of charge. On the Xcode page select the button to get the
package. Follow the usual procedure to start the download. Once the download
has finished open the applications folder and select the "Install Xcode" entry.
In contrast to the Xcode 3 procedure described above, the installer does not
ask for a selection of sub-packages.


2. Install Python 3.4
---------------------
Although Mac OS X comes with a python installation it is recommended to
install the python package provided by the Python community. Download it
from 

http://www.python.org/download/

After the download finished open the downloaded package and install it.

Note: The Python documentation can be found in these locations

/Library/Frameworks/Python.framework/Versions/3.4/Resources/English.lproj/Documentation/index.html
/Applications/Python 3.4/Python Documentation.html

3. Install Qt5
--------------
Download the Qt5 package from

http://www.qt.io/download/

After the download finished open the downloaded package and install it. The
tools (e.g. Designer, Linguist) can be found in the location

| ˜/Qt<version>/<version>/<compiler>/bin
| e.g. ˜/Qt5.3.0/5.3.0/clang_64/bin

The documentation can be found in these locations

˜/Qt<version>/<version>/<compiler>/qtdoc (HTML format)
˜/Qt<version>/<version>/<compiler>/ (QtHelp format)

The translation files can be found in this location

˜/Qt<version>/<version>/<compiler>//translations


4. Install QScintilla2
----------------------
Download the QScintilla2 source code package from

http://www.riverbankcomputing.com/software/qscintilla/download

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the Qt4Qt5 directory within the extracted folder and enter these commands in a
terminal window

::

    qmake qscintilla.pro
    make -j x (number of cores including hyper threaded ones)
    sudo make install


5. Install sip
--------------
Download the sip source code package from

http://www.riverbankcomputing.com/software/sip/download

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the extracted folder and enter these commands in a terminal window

::

    python3 configure.py
    make -j x (number of cores including hyper threaded ones)
    sudo make install


6. Install PyQt5
----------------
Download the PyQt5 source code package from

http://www.riverbankcomputing.com/software/pyqt/download5

After the download has finished open a Finder window and extract the downloaded
archive in the Downloads folder (or any other folder of your choice). Change to
the extracted folder and enter these commands in a terminal window

::

    python3 configure.py -c -j x (number of cores including hyper threaded ones)
    make -j x (number of cores including hyper threaded ones)
    sudo make install


7. Install QScintilla2 Python bindings
--------------------------------------
Change back to the extracted QScintilla2 directory and in there change to the
Python subdirectory. Enter these commands in a terminal window

::

    python3 configure.py --pyqt=PyQt5 -c -j x (number of cores including hyper threaded ones)
    make -j x (number of cores including hyper threaded ones)
    sudo make install


8. Install MacPorts
-------------------
MacPorts is a packaging system for the Mac. I recommend to install it to use
some applications and libraries, that are a bit tricky to compile from source
or for which the supplier doesn't offer ready built Mac OS X packages. In order
to install MacPorts get the proper disk image (for Lion or Snow Leopard) from

http://www.macports.org/install.php

and install it with the usual procedure. You may read about it's usage via

http://guide.macports.org/#using.port

For a recipe on how to update MacPorts and the installed ports see the end
of this file (Appendix A)


9. Install aspell and dictionaries
-----------------------------------
eric6 includes the capability to perform spell checking of certain parts of
the sources. This is done via enchant which works with various spell checking
libraries as it's backend. It depends upon aspell and hunspell. In order to 
install aspell enter this command in a terminal window

::

    sudo port install aspell

This installs aspell and a bunch of dependancies. Once aspell has been installed
install the dictionaries of your desire. To get a list of available dictionaries
enter

::

    port search aspell-dict

Then install them with a command like this

::

    sudo port install aspell-dict-de aspell-dict-en


10. Install hunspell and dictionaries
-------------------------------------
pyenchant depends on hunspell as well. Enter these commands to install it

::

    sudo port install hunspell

This installs hunspell and a bunch of dependancies. Once hunspell has been
installed, install the dictionaries of your desire. To get a list of hunspell
dictionaries enter

::

    port search hunspell-dict

Then install them with a command like this

::

    sudo port install hunspell-dict-de_DE

replacing the 'de_DE' part with the language code of your desire.


11. Install enchant
-------------------
In order to install enchant and penchant via MacPorts enter these commands

::

    sudo port install enchant


12. Install pyenchant
---------------------
Install ``pyenchant`` using the ``pip`` utility. To do this just enter this
in a console window

::

    sudo pip3 install pyenchant

In order to test, if everything worked ok open a Python shell and enter
these commands

>>> import enchant
>>> enchant.list_dicts()

If you get an error (ImportError for the first command or no dictionaries
are show for the second command) please recheck the installation checks.


13. Install pysvn
-----------------
Mac OS X already provides subversion. However, best performance for eric6 is
gained with the pysvn interface to subversion. Therefore it is recommended to
install pysvn. Get pysvn via 

http://pysvn.tigris.org/project_downloads.html

After the download finished open the downloaded package and install it.

In order to test, if everything worked ok, open a Python shell and enter these
commands

>>> import pysvn
>>> pysvn.version

This should print the pysvn version as a tuple like ``(1, 7, 10, 1584)``. If
you get an error please check your installation.

Note: Mac OS X Lion provides Subversion 1.6.x. When downloading pysvn make sure
      to download the variant compiled against that version. This is important
      because the working copy format of Subversion 1.7.x is incompatible to
      the old one.


14. Install Mercurial
---------------------
Get Mercurial from

http://mercurial.selenic.com/

Extract the downloaded package and install it.


15. Install eric6
-----------------
Get the latest eric6 distribution package from 

http://eric-ide.python-projects.org/eric-download.html

Just follow the link on this page to the latest download.

Extract the downloaded package and language packs into a directory and install
it with this command

::

    sudo python3 install.py

This step concludes the installation procedure. You are ready for the first
start of eric6.

The eric6 installer created an application bundle in the location

::

    /Applications/eric6

You may drag it to the dock to have it ready.


16. First start of eric6
------------------------
When eric6 is started for the first time it will recognize that it hasn't been
configured yet. Therefore it will start the configuration dialog with the
default configuration. At this point you could simply close the dialog by
pressing the OK button. However, it is strongly recommended that you go through
the configuration pages to get a feeling for the configuration possibilities.

It is recommended to configure at least the path to the Qt tools on the Qt page
and the paths to the various help pages on the Help Documentation page. The
values to be entered are given above in the Python and Qt installation
sections.


17. Install optional packages for eric6 (for plug-ins)
------------------------------------------------------
eric6 provides an extension mechanism via plug-ins. Some of them require the
installation of additional python packages. The plug-ins themselves are
available via the Plugin Repository from within eric6.


17.1 Installation of pylint
~~~~~~~~~~~~~~~~~~~~~~~~~~~
pylint is a tool to check Python sources for issues. Install ``pylint`` using
the ``pip`` utility. To do this just enter this in a console window

::

    sudo pip3 install pylint


17.2 Installation of cx_Freeze
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cx_Freeze is a tool that packages a Python application into executables. It is
like py2exe and py2app. Install ``cx_Freeze`` using the ``pip`` utility. To do
this just enter this in a console window

::

    sudo pip3 install cx_Freeze

This completes this installation instruction. Please enjoy using eric6 and let
the world know about it.


Appendix A: Update of MacPorts
------------------------------
In order to update MacPorts and the installed packages enter these commands in
a terminal window

::

    sudo port selfupdate        (update MacPorts itself)
    sudo port upgrade outdated  (update outdated installed ports)
