import os
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QPixmap
from .Ui_AboutPymakr import Ui_AboutPymakr
from UI import Info

descriptionText = """
<html>
  <head/>
  <body>
    <p>An editor to work with Pycom products.</p>
    <p>This program makes use of the following Open Source Software:<br/><a href="http://www.qt.io"><span style=" text-decoration: underline; color:#ffffff;">Qt</span></a>, <a href="https://www.riverbankcomputing.com/software/pyqt"><span style=" text-decoration: underline; color:#ffffff;">PyQt</span></a>, and <a href="https://www.riverbankcomputing.com/software/qscintilla"><span style=" text-decoration: underline; color:#ffffff;">QScintilla2</span></a>, available under the GNU GPL v3 license.</p>
    <p>Based on <a href="http://eric-ide.python-projects.org/"><span style=" text-decoration: underline; color:#ffffff;">Eric IDE</span></a>.<br/>Copyright (c) 2002 - 2016 Detlev Offenbach.</p>
    <p>Aditional portions Copyright (c) 2016 <a href="http://www.pycom.io/"><span style=" text-decoration: underline; color:#ffffff;">Pycom</span></a>.<br/></p>
  </body>
</html>
"""

class AboutPymakr(QDialog, Ui_AboutPymakr):
    """
    Class implementing an 'About Pymakr' dialog.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(AboutPymakr, self).__init__(parent)
        self.setupUi(self)
        self.__path = os.path.dirname(os.path.realpath(__file__))
        self.setWindowTitle(self.tr("About Pymakr"))
        self.lblTitle.setText(Info.Builder + " " + Info.Program)
        self.lblVersion.setText(self.tr("Version ") + Info.Version)
        self.lblDescription.setText(self.tr(descriptionText))
        self.lblDescription.setOpenExternalLinks(True)
        self.imgIcon.setPixmap(QPixmap(self.__path + '/img/icon.png').scaled(80, 80))