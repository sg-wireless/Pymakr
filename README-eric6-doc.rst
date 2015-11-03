================================================
README for the eric6-doc documentation generator
================================================

eric6-doc is the documentation generator of the eric6 IDE. Python source
code documentation may be included as ordinary Python doc-strings or as 
documentation comments. For Quixote Template files (PTL) only documentation 
comments are available due to the inner workings of Quixote. Documentation 
comments start with the string ###, followed by the contents and ended by 
###. Every line of the documentation comments contents must start with a # 
(see example below).

For Ruby files, the documentation string must be started with "=begin edoc"
and must be ended with "=end". The documentation string for classes, modules
and functions/methods must follow their defininition.

Documentation for packages (i.e. directories) must be in a file called 
__init__.py or __init__.rb. If a package directory doesn't contain a file
like these, documentation for files in this directory is suppressed.

The documentation consist of two parts. The first part is the description of 
the module, class, function or method. The second part, separated from the 
first by a blank line, consists of one or more tags. These are described below.

eric6-doc produces HTML files from the documentation found within the source 
files scaned. It understands the following commandline parameters next to
others.

-o directory
  Generate files in the named directory.

-R, -r
  Perform a recursive search for Python files.

-x directory
  Specify a directory basename to be excluded. This option may be repeated
  multiple times.

-i
  Don't generate index files.

Just type "eric6-doc" to get some usage information.

1. Description
--------------
The descriptions are HTML fragments and may contain most standard HTML. The
description text is included in the output wrapped in P tags, but unchanged 
otherwise. Paragraphs have to be separated by a blank line. In order to
generate a blank line in the output enter a line that contains a single dot
(.). Reserved HTML entities (<, > and &) and the at-sign (@) at the beginning 
of a line, if that line doesn't contain a tag (see below), must be properly 
escaped. "<" should be written as "&lt;", ">" as "&gt;", "&" as "&amp;" and
"@" should be escaped as "@@".

The documentation string or documentation comment may contain block tags
and inline tags. Inline tags are denoted by curly braces and can be placed
anywhere in the main description or in the description part of block tags.
Block tags can only be placed in the tag section that follows the main
description. Block tags are indicated by an at-sign (@) at the beginning of
the line. The text before the first tag is the description of a module, class,
method or function.

Python Docstring::

    """
    This is sentence one, which gets included as a short description.
    All additional sentences are included into the full description.
    
    @param param1 first parameter
    @exception ValueError list entry wasn't found
    @return flag indicating success
    """
    
Python/Quixote Documentation comment::

    ###
    # This is line one, which gets included as a short description.
    # All additional lines are included into the full description.
    #
    # @param param1 first parameter
    # @exception ValueError list entry wasn't found
    # @return flag indicating success
    ###
    
Ruby Docstring::

    =begin edoc
    This is line one, which gets included as a short description.
    All additional lines are included into the full description.
    
    @param param1 first parameter
    @exception ValueError list entry wasn't found
    @return flag indicating success
    =end

2. Block Tags
-------------
The block tags recogized by eric6-doc are:

@@

    This isn't really a tag. This is used to escape an at sign at the beginning
    of a line. Everything after the first @ is copied verbatim to the output.

@author author

    This tag is used to name the author of the code. For example::
    
    @author Detlev Offenbach <detlev@die-offenbachs.de>

@deprecated description

    This tag is used to mark a function or method as deprecated. It is always 
    followed by one or more lines of descriptive text.

@event eventname description

    This tag is used to describe the events (PyQt) a class may emit. It is 
    always followed by the event name and one or more lines of descriptive 
    text. For example::
    
    @event closeEvent Emitted when an editor window is closed.

@exception exception description

    These tags are used to describe the exceptions a function or method may 
    raise. It is always followed by the exception name and one or more lines 
    of descriptive text. For example::
    
    @exception ValueError The searched value is not contained in the list.

@ireturn description

    This tag is an alias for the @return tag.

@keyparam name description

    This tag is like the @param tag, but should be used for parameters, that 
    should always be given as keyword parameters. It is always followed by 
    the argument name and one or more lines of descriptive text. For example::
    
    @keyparam extension Optional extension of the source file.

@param name description

    This tag is used to describe a function or method argument. It is always 
    followed by the argument name and one or more lines of descriptive text.
    For example::
    
    @param filename name of the source file

@ptype name parameter-type

    This tag is used to describe the type of  a function or method argument.
    It is always followed by the argument name and type. The argument has
    to be defined already with @param or @keyparam. For example::
    
    @ptype filename str

@raise exception description

    This tag is an alias for the @exception tag.

@return description

    This tag is used to describe a function or method return value. It can 
    include one or more lines of descriptive text. For example::
    
    @return list of file names

@rtype type

    This tag is used to describe a function or method return type. It should
    follow an @return tag. For
    example::
    
    @rtype list of str

@see reference

    This tag is used to include a reference in the documentation. It comes in
    three different forms.

    @see "string"
    
        Adds a text entry of string. No link is generated. eric6-doc
        distinguishes this form from the others by looking for a double-quote
        (") as the first character. For example:

        @see "eric6-doc readme file"

    @see <a href="URL#value">label</a>
    
        Adds a link as defined by URL#value. eric6-doc distinguishes this form
        from the others by looking for a less-than symbol (<) as the first
        character. For example::

        @see <a href="eric6.eric6-doc.html>eric6-doc documentation generator</a>

    @see package.module#member label
    
        Adds a link to "member" in "module" in "package". package can be a
        package path, where the package names are separated by a dot character
        (.). The "package.module#member" part must not be split over several
        lines and must name a valid target within the documentation directory.
        For example::

        @see eric6.eric6-doc#main eric6-doc main() function
        @see eric6.DocumentationTools.ModuleDocumentor#ModuleDocument.__genModuleSection ModuleDocument.__genModuleSection

@signal signalname description

    This tag is used to describe the signals (PyQt) a class may emit. It is 
    always followed by the signal name and one or more lines of descriptive 
    text. For example::
    
    @signal lastEditorClosed Emitted after the last editor window was closed.

@throws exception description

    This tag is an alias for the @exception tag.

@type parameter-type

    This tag is used to give the type of the parameter just described.
    It must be preceded by a @param or @keyparam tag. For example::
    
    @param filename name of the source file
    @type str

3. Inline Tags
--------------
The inline tags recogized by eric6-doc are:

{@link package.module#member label}

    Inserts an in-line link with visible text label that points to the documentation
    given in the reference. This tag works he same way as the @see block tag of this
    form.
