# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to enter personal data.
"""

from __future__ import unicode_literals

from PyQt5.QtWidgets import QDialog

from .Ui_PersonalDataDialog import Ui_PersonalDataDialog

import UI.PixmapCache
import Preferences


class PersonalDataDialog(QDialog, Ui_PersonalDataDialog):
    """
    Class implementing a dialog to enter personal data.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(PersonalDataDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.iconLabel.setPixmap(UI.PixmapCache.getPixmap("pim48.png"))
        
        self.firstnameEdit.setText(Preferences.getHelp("PimFirstName"))
        self.lastnameEdit.setText(Preferences.getHelp("PimLastName"))
        self.fullnameEdit.setText(Preferences.getHelp("PimFullName"))
        self.emailEdit.setText(Preferences.getHelp("PimEmail"))
        self.phoneEdit.setText(Preferences.getHelp("PimPhone"))
        self.mobileEdit.setText(Preferences.getHelp("PimMobile"))
        self.addressEdit.setText(Preferences.getHelp("PimAddress"))
        self.cityEdit.setText(Preferences.getHelp("PimCity"))
        self.zipEdit.setText(Preferences.getHelp("PimZip"))
        self.stateEdit.setText(Preferences.getHelp("PimState"))
        self.countryEdit.setText(Preferences.getHelp("PimCountry"))
        self.homepageEdit.setText(Preferences.getHelp("PimHomePage"))
        self.special1Edit.setText(Preferences.getHelp("PimSpecial1"))
        self.special2Edit.setText(Preferences.getHelp("PimSpecial2"))
        self.special3Edit.setText(Preferences.getHelp("PimSpecial3"))
        self.special4Edit.setText(Preferences.getHelp("PimSpecial4"))
    
    def storeData(self):
        """
        Public method to store the entered personal information.
        """
        Preferences.setHelp("PimFirstName", self.firstnameEdit.text())
        Preferences.setHelp("PimLastName", self.lastnameEdit.text())
        Preferences.setHelp("PimFullName", self.fullnameEdit.text())
        Preferences.setHelp("PimEmail", self.emailEdit.text())
        Preferences.setHelp("PimPhone", self.phoneEdit.text())
        Preferences.setHelp("PimMobile", self.mobileEdit.text())
        Preferences.setHelp("PimAddress", self.addressEdit.text())
        Preferences.setHelp("PimCity", self.cityEdit.text())
        Preferences.setHelp("PimZip", self.zipEdit.text())
        Preferences.setHelp("PimState", self.stateEdit.text())
        Preferences.setHelp("PimCountry", self.countryEdit.text())
        Preferences.setHelp("PimHomePage", self.homepageEdit.text())
        Preferences.setHelp("PimSpecial1", self.special1Edit.text())
        Preferences.setHelp("PimSpecial2", self.special2Edit.text())
        Preferences.setHelp("PimSpecial3", self.special3Edit.text())
        Preferences.setHelp("PimSpecial4", self.special4Edit.text())
