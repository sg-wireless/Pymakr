# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to show some template help.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from .Ui_TemplateHelpDialog import Ui_TemplateHelpDialog


class TemplateHelpDialog(QDialog, Ui_TemplateHelpDialog):
    """
    Class implementing a dialog to show some template help.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(TemplateHelpDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        
        self.helpEdit.setHtml(self.tr(
            """<p>To use variables in a template, you just have to"""
            """ enclose the variablename with $-characters. When you"""
            """ use the template, you will then be asked for a value"""
            """ for this variable.</p>"""
            """<p>Example template: This is a $VAR$</p>"""
            """<p>When you use this template you will be prompted for"""
            """ a value for the variable $VAR$. Any occurrences of $VAR$"""
            """ will then be replaced with whatever you've entered.</p>"""
            """<p>If you need a single $-character in a template, which"""
            """ is not used to enclose a variable, type $$(two dollar"""
            """ characters) instead. They will automatically be replaced"""
            """ with a single $-character when you use the template.</p>"""
            """<p>If you want a variables contents to be treated"""
            """ specially, the variablename must be followed by a ':'"""
            """ and one formatting specifier (e.g. $VAR:ml$). The"""
            """ supported specifiers are:"""
            """<table>"""
            """<tr><td>ml</td><td>Specifies a multiline formatting."""
            """ The first line of the variable contents is prefixed with"""
            """ the string occurring before the variable on the same"""
            """ line of the template. All other lines are prefixed by"""
            """ the same amount of whitespace as the line containing"""
            """ the variable."""
            """</td></tr>"""
            """<tr><td>rl</td><td>Specifies a repeated line formatting."""
            """ Each line of the variable contents is prefixed with the"""
            """ string occuring before the variable on the same line of"""
            """ the template."""
            """</td></tr>"""
            """</table></p>"""
            """<p>The following predefined variables may be used in a"""
            """ template:"""
            """<table>"""
            """<tr><td>date</td>"""
            """<td>today's date in ISO format (YYYY-MM-DD)</td></tr>"""
            """<tr><td>year</td>"""
            """<td>the current year</td></tr>"""
            """<tr><td>project_name</td>"""
            """<td>the name of the project (if any)</td></tr>"""
            """<tr><td>project_path</td>"""
            """<td>the path of the project (if any)</td></tr>"""
            """<tr><td>path_name</td>"""
            """<td>full path of the current file</td></tr>"""
            """<tr><td>dir_name</td>"""
            """<td>full path of the parent directory</td></tr>"""
            """<tr><td>file_name</td>"""
            """<td>the current file name (without directory)</td></tr>"""
            """<tr><td>base_name</td>"""
            """<td>like <i>file_name</i>, but without extension"""
            """</td></tr>"""
            """<tr><td>ext</td>"""
            """<td>the extension of the current file</td></tr>"""
            """<tr><td>cur_select</td>"""
            """<td>the currently selected text</td></tr>"""
            """<tr><td>insertion</td>"""
            """<td>Sets insertion point for cursor after template is"""
            """ inserted.</td>"""
            """</tr>"""
            """<tr><td>select_start</td>"""
            """<td>Sets span of selected text in template after template"""
            """ is inserted (used together with 'select_end').</td></tr>"""
            """<tr><td>select_end</td>"""
            """<td>Sets span of selected text in template after template"""
            """ is inserted (used together with 'select_start')."""
            """</td></tr>"""
            """<tr><td>clipboard</td>"""
            """<td>the text of the clipboard</td></tr>"""
            """</table></p>"""
            """<p>If you want to change the default delimiter to"""
            """ anything different, please use the configuration"""
            """ dialog to do so.</p>"""
        ))
