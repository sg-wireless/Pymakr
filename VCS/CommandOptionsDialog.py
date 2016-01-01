# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the VCS command options dialog.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_CommandOptionsDialog import Ui_VcsCommandOptionsDialog

import Utilities


class VcsCommandOptionsDialog(QDialog, Ui_VcsCommandOptionsDialog):
    """
    Class implementing the VCS command options dialog.
    """
    def __init__(self, vcs, parent=None):
        """
        Constructor
        
        @param vcs reference to the vcs object
        @param parent parent widget (QWidget)
        """
        super(VcsCommandOptionsDialog, self).__init__(parent)
        self.setupUi(self)
        
        opt = vcs.vcsGetOptions()
        self.globalEdit.setText(" ".join(opt['global']))
        self.commitEdit.setText(" ".join(opt['commit']))
        self.checkoutEdit.setText(" ".join(opt['checkout']))
        self.updateEdit.setText(" ".join(opt['update']))
        self.addEdit.setText(" ".join(opt['add']))
        self.removeEdit.setText(" ".join(opt['remove']))
        self.diffEdit.setText(" ".join(opt['diff']))
        self.logEdit.setText(" ".join(opt['log']))
        self.historyEdit.setText(" ".join(opt['history']))
        self.statusEdit.setText(" ".join(opt['status']))
        self.tagEdit.setText(" ".join(opt['tag']))
        self.exportEdit.setText(" ".join(opt['export']))
        
        # modify the what's this help
        for widget in [self.globalEdit, self.commitEdit, self.checkoutEdit,
                       self.updateEdit, self.addEdit, self.removeEdit,
                       self.diffEdit, self.logEdit, self.historyEdit,
                       self.statusEdit, self.tagEdit, self.exportEdit]:
            t = widget.whatsThis()
            if t:
                t += Utilities.getPercentReplacementHelp()
                widget.setWhatsThis(t)
        
        msh = self.minimumSizeHint()
        self.resize(max(self.width(), msh.width()), msh.height())
        
    def getOptions(self):
        """
        Public method used to retrieve the entered options.
        
        @return dictionary of strings giving the options for each supported
            vcs command
        """
        opt = {}
        opt['global'] = Utilities.parseOptionString(self.globalEdit.text())
        opt['commit'] = Utilities.parseOptionString(self.commitEdit.text())
        opt['checkout'] = Utilities.parseOptionString(self.checkoutEdit.text())
        opt['update'] = Utilities.parseOptionString(self.updateEdit.text())
        opt['add'] = Utilities.parseOptionString(self.addEdit.text())
        opt['remove'] = Utilities.parseOptionString(self.removeEdit.text())
        opt['diff'] = Utilities.parseOptionString(self.diffEdit.text())
        opt['log'] = Utilities.parseOptionString(self.logEdit.text())
        opt['history'] = Utilities.parseOptionString(self.historyEdit.text())
        opt['status'] = Utilities.parseOptionString(self.statusEdit.text())
        opt['tag'] = Utilities.parseOptionString(self.tagEdit.text())
        opt['export'] = Utilities.parseOptionString(self.exportEdit.text())
        return opt
