README for passive mode debugging
=================================

eric6 provides the capability to debug programms using the passive
mode. In this mode it is possible to start the debugger separate from
the IDE. This may be done on a different computer as well. If the
debugger is started on a remote machine, it is your responsibility
to ensure, that the paths to the script to be debugged are identical
on both machines.

In order to enable passive mode debugging in the IDE choose the
debugger tab of the preferences dialog and enable the passive mode
debugging checkbox. You may change the default port as well. Please
be aware that you have to tell the debugger the port, if it is different to the 
default value of 42424.

On the remote computer you have to have the debugger scripts installed.
Use DebugClient.py to debug normal scripts or DebugClientThreads.py
to debug multi threaded scripts. The debuggers know about the following
commandline switches.

::

    -h <hostname>
        This specifies the hostname of the machine running the IDE.
    -p <portnumber>
        This specifies the portnumber of the IDE.
    -w <directory>
        This specifies the working directory to be used for the script
        to be debugged.
    -t
        This enables tracing into the Python library.
    -n
        This disables the redirection of stdin, stdout and stderr.
    -e
        This disables reporting of exceptions.
    --fork-child
        This tells the debugger to follow the child when forking.
    --fork-parent
        This tells the debugger to follow the parent when forking

The commandline parameters have to be followed by ``'--'`` (double dash),
the script to be debugged and its commandline parameters.

Example::

    python DebugClient -h somehost -- myscript.py param1
    
After the execution of the debugger command, it connects to the IDE and
tells it the filename of the script being debugged. The IDE will try to load it
and the script will stop at the first line. After that you may set breakpoints,
step through your script and use all the debugging functions.

Note: The port and hostname may alternatively be set through the environment
variables ERICPORT and ERICHOST.

Please send bug reports, feature requests or contributions to eric bugs address
<eric-bugs@die-offenbachs.de> or using the buildt in bug reporting dialog.
