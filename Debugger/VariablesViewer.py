# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the variables viewer widget.
"""

from __future__ import unicode_literals
try:
    str = unicode
except NameError:
    pass

from PyQt5.QtCore import Qt, QRegExp, qVersion, QCoreApplication
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, \
    QMenu
from PyQt5.QtGui import QTextDocument   # __IGNORE_WARNING__

from E5Gui.E5Application import e5App

from DebugClients.Python3.DebugConfig import ConfigVarTypeStrings
    
from .Config import ConfigVarTypeDispStrings

import Preferences
import Utilities


class VariableItem(QTreeWidgetItem):
    """
    Class implementing the data structure for variable items.
    """
    def __init__(self, parent, dvar, dvalue, dtype):
        """
        Constructor
        
        @param parent reference to the parent item
        @param dvar variable name (string)
        @param dvalue value string (string)
        @param dtype type string (string)
        """
        self.__value = dvalue
        if len(dvalue) > 2048:     # 1024 * 2
            dvalue = QCoreApplication.translate(
                "VariableItem", "<double click to show value>")
            self.__tooltip = dvalue
        else:
            if Qt.mightBeRichText(dvalue):
                self.__tooltip = Utilities.html_encode(dvalue)
            else:
                self.__tooltip = dvalue
            lines = dvalue.splitlines()
            if len(lines) > 1:
                # only show the first non-empty line;
                # indicate skipped lines by <...> at the
                # beginning and/or end
                index = 0
                while index < len(lines) - 1 and lines[index] == "":
                    index += 1
                dvalue = ""
                if index > 0:
                    dvalue += "<...>"
                dvalue += lines[index]
                if index < len(lines) - 1:
                    dvalue += "<...>"
        
        super(VariableItem, self).__init__(parent, [dvar, dvalue, dtype])
        
        self.populated = True
        
    def getValue(self):
        """
        Public method to return the value of the item.
        
        @return value of the item (string)
        """
        return self.__value
        
    def data(self, column, role):
        """
        Public method to return the data for the requested role.
        
        This implementation changes the original behavior in a way, that the
        display data is returned as the tooltip for column 1.
        
        @param column column number (integer)
        @param role data role (Qt.ItemDataRole)
        @return requested data
        """
        if column == 1 and role == Qt.ToolTipRole:
            return self.__tooltip
        return super(VariableItem, self).data(column, role)
        
    def attachDummy(self):
        """
        Public method to attach a dummy sub item to allow for lazy population.
        """
        QTreeWidgetItem(self, ["DUMMY"])
        
    def deleteChildren(self):
        """
        Public method to delete all children (cleaning the subtree).
        """
        for itm in self.takeChildren():
            del itm
        
    def key(self, column):
        """
        Public method generating the key for this item.
        
        @param column the column to sort on (integer)
        @return text of the column (string)
        """
        return self.text(column)
        
    def __lt__(self, other):
        """
        Special method to check, if the item is less than the other one.
        
        @param other reference to item to compare against (QTreeWidgetItem)
        @return true, if this item is less than other (boolean)
        """
        column = self.treeWidget().sortColumn()
        return self.key(column) < other.key(column)
        
    def expand(self):
        """
        Public method to expand the item.
        
        Note: This is just a do nothing and should be overwritten.
        """
        return
        
    def collapse(self):
        """
        Public method to collapse the item.
        
        Note: This is just a do nothing and should be overwritten.
        """
        return


class SpecialVarItem(VariableItem):
    """
    Class implementing a VariableItem that represents a special variable node.
    
    These special variable nodes are generated for classes, lists,
    tuples and dictionaries.
    """
    def __init__(self, parent, dvar, dvalue, dtype, frmnr, scope):
        """
        Constructor
        
        @param parent parent of this item
        @param dvar variable name (string)
        @param dvalue value string (string)
        @param dtype type string (string)
        @param frmnr frame number (0 is the current frame) (int)
        @param scope flag indicating global (1) or local (0) variables
        """
        VariableItem.__init__(self, parent, dvar, dvalue, dtype)
        self.attachDummy()
        self.populated = False
        
        self.framenr = frmnr
        self.scope = scope

    def expand(self):
        """
        Public method to expand the item.
        """
        self.deleteChildren()
        self.populated = True
        
        pathlist = [self.text(0)]
        par = self.parent()
        
        # step 1: get a pathlist up to the requested variable
        while par is not None:
            pathlist.insert(0, par.text(0))
            par = par.parent()
        
        # step 2: request the variable from the debugger
        filter = e5App().getObject("DebugUI").variablesFilter(self.scope)
        e5App().getObject("DebugServer").remoteClientVariable(
            self.scope, filter, pathlist, self.framenr)


class ArrayElementVarItem(VariableItem):
    """
    Class implementing a VariableItem that represents an array element.
    """
    def __init__(self, parent, dvar, dvalue, dtype):
        """
        Constructor
        
        @param parent parent of this item
        @param dvar variable name (string)
        @param dvalue value string (string)
        @param dtype type string (string)
        """
        VariableItem.__init__(self, parent, dvar, dvalue, dtype)
        
        """
        Array elements have numbers as names, but the key must be
        right justified and zero filled to 6 decimal places. Then
        element 2 will have a key of '000002' and appear before
        element 10 with a key of '000010'
        """
        keyStr = self.text(0)
        self.arrayElementKey = "{0:6d}".format(int(keyStr))

    def key(self, column):
        """
        Public method generating the key for this item.
        
        @param column the column to sort on (integer)
        @return key of the item (string)
        """
        if column == 0:
            return self.arrayElementKey
        else:
            return VariableItem.key(self, column)


class SpecialArrayElementVarItem(SpecialVarItem):
    """
    Class implementing a QTreeWidgetItem that represents a special array
    variable node.
    """
    def __init__(self, parent, dvar, dvalue, dtype, frmnr, scope):
        """
        Constructor
        
        @param parent parent of this item
        @param dvar variable name (string)
        @param dvalue value string (string)
        @param dtype type string (string)
        @param frmnr frame number (0 is the current frame) (int)
        @param scope flag indicating global (1) or local (0) variables
        """
        SpecialVarItem.__init__(self, parent, dvar, dvalue, dtype, frmnr,
                                scope)
        
        """
        Array elements have numbers as names, but the key must be
        right justified and zero filled to 6 decimal places. Then
        element 2 will have a key of '000002' and appear before
        element 10 with a key of '000010'
        """
        keyStr = self.text(0)[:-2]  # strip off [], () or {}
        self.arrayElementKey = "{0:6d}".format(int(keyStr))

    def key(self, column):
        """
        Public method generating the key for this item.
        
        @param column the column to sort on (integer)
        @return key of the item (string)
        """
        if column == 0:
            return self.arrayElementKey
        else:
            return SpecialVarItem.key(self, column)


class VariablesViewer(QTreeWidget):
    """
    Class implementing the variables viewer widget.
    
    This widget is used to display the variables of the program being
    debugged in a tree. Compound types will be shown with
    their main entry first. Once the subtree has been expanded, the
    individual entries will be shown. Double clicking an entry will
    popup a dialog showing the variables parameters in a more readable
    form. This is especially useful for lengthy strings.
    
    This widget has two modes for displaying the global and the local
    variables.
    """
    def __init__(self, parent=None, scope=1):
        """
        Constructor
        
        @param parent the parent (QWidget)
        @param scope flag indicating global (1) or local (0) variables
        """
        super(VariablesViewer, self).__init__(parent)
        
        self.indicators = {'list': '[]', 'tuple': '()', 'dict': '{}',
                           # Python types
                           'Array': '[]', 'Hash': '{}'
                           # Ruby types
                           }
        
        self.rx_class = QRegExp('<.*(instance|object) at 0x.*>')
        self.rx_class2 = QRegExp('class .*')
        self.rx_class3 = QRegExp('<class .* at 0x.*>')
        self.dvar_rx_class1 = QRegExp(
            r'<.*(instance|object) at 0x.*>(\[\]|\{\}|\(\))')
        self.dvar_rx_class2 = QRegExp(r'<class .* at 0x.*>(\[\]|\{\}|\(\))')
        self.dvar_rx_array_element = QRegExp(r'^\d+$')
        self.dvar_rx_special_array_element = QRegExp(r'^\d+(\[\]|\{\}|\(\))$')
        self.rx_nonprintable = QRegExp(r"""(\\x\d\d)+""")
        
        self.framenr = 0
        
        self.loc = Preferences.getSystem("StringEncoding")
        
        self.openItems = []
        
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        self.scope = scope
        if scope:
            self.setWindowTitle(self.tr("Global Variables"))
            self.setHeaderLabels([
                self.tr("Globals"),
                self.tr("Value"),
                self.tr("Type")])
            self.setWhatsThis(self.tr(
                """<b>The Global Variables Viewer Window</b>"""
                """<p>This window displays the global variables"""
                """ of the debugged program.</p>"""
            ))
        else:
            self.setWindowTitle(self.tr("Local Variables"))
            self.setHeaderLabels([
                self.tr("Locals"),
                self.tr("Value"),
                self.tr("Type")])
            self.setWhatsThis(self.tr(
                """<b>The Local Variables Viewer Window</b>"""
                """<p>This window displays the local variables"""
                """ of the debugged program.</p>"""
            ))
        
        header = self.header()
        header.setSortIndicator(0, Qt.AscendingOrder)
        header.setSortIndicatorShown(True)
        if qVersion() >= "5.0.0":
            header.setSectionsClickable(True)
        else:
            header.setClickable(True)
        header.resizeSection(0, 120)    # variable column
        header.resizeSection(1, 150)    # value column
        
        self.__createPopupMenus()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        
        self.itemExpanded.connect(self.__expandItemSignal)
        self.itemCollapsed.connect(self.collapseItem)
        
        self.resortEnabled = True
        
    def __createPopupMenus(self):
        """
        Private method to generate the popup menus.
        """
        self.menu = QMenu()
        self.menu.addAction(self.tr("Show Details..."), self.__showDetails)
        self.menu.addSeparator()
        self.menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.backMenu = QMenu()
        self.backMenu.addAction(self.tr("Configure..."), self.__configure)
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        gcoord = self.mapToGlobal(coord)
        if self.itemAt(coord) is not None:
            self.menu.popup(gcoord)
        else:
            self.backMenu.popup(gcoord)
        
    def __findItem(self, slist, column, node=None):
        """
        Private method to search for an item.
        
        It is used to find a specific item in column,
        that is a child of node. If node is None, a child of the
        QTreeWidget is searched.
        
        @param slist searchlist (list of strings)
        @param column index of column to search in (int)
        @param node start point of the search
        @return the found item or None
        """
        if node is None:
            count = self.topLevelItemCount()
        else:
            count = node.childCount()
        
        for index in range(count):
            if node is None:
                itm = self.topLevelItem(index)
            else:
                itm = node.child(index)
            if itm.text(column) == slist[0]:
                if len(slist) > 1:
                    itm = self.__findItem(slist[1:], column, itm)
                return itm
        
        return None
        
    def showVariables(self, vlist, frmnr):
        """
        Public method to show variables in a list.
        
        @param vlist the list of variables to be displayed. Each
                listentry is a tuple of three values.
                <ul>
                <li>the variable name (string)</li>
                <li>the variables type (string)</li>
                <li>the variables value (string)</li>
                </ul>
        @param frmnr frame number (0 is the current frame) (int)
        """
        self.current = self.currentItem()
        if self.current:
            self.curpathlist = self.__buildTreePath(self.current)
        self.clear()
        self.__scrollToItem = None
        self.framenr = frmnr
        
        if len(vlist):
            self.resortEnabled = False
            for (var, vtype, value) in vlist:
                self.__addItem(None, vtype, var, value)
            
            # reexpand tree
            openItems = sorted(self.openItems[:])
            self.openItems = []
            for itemPath in openItems:
                itm = self.__findItem(itemPath, 0)
                if itm is not None:
                    self.expandItem(itm)
                else:
                    self.openItems.append(itemPath)
            
            if self.current:
                citm = self.__findItem(self.curpathlist, 0)
                if citm:
                    self.setCurrentItem(citm)
                    citm.setSelected(True)
                    self.scrollToItem(citm, QAbstractItemView.PositionAtTop)
                    self.current = None
            
            self.resortEnabled = True
            self.__resort()

    def showVariable(self, vlist):
        """
        Public method to show variables in a list.
        
        @param vlist the list of subitems to be displayed.
                The first element gives the path of the
                parent variable. Each other listentry is
                a tuple of three values.
                <ul>
                <li>the variable name (string)</li>
                <li>the variables type (string)</li>
                <li>the variables value (string)</li>
                </ul>
        """
        resortEnabled = self.resortEnabled
        self.resortEnabled = False
        if self.current is None:
            self.current = self.currentItem()
            if self.current:
                self.curpathlist = self.__buildTreePath(self.current)
        
        if vlist:
            itm = self.__findItem(vlist[0], 0)
            for var, vtype, value in vlist[1:]:
                self.__addItem(itm, vtype, var, value)

        # reexpand tree
        openItems = sorted(self.openItems[:])
        self.openItems = []
        for itemPath in openItems:
            itm = self.__findItem(itemPath, 0)
            if itm is not None and not itm.isExpanded():
                if itm.populated:
                    self.blockSignals(True)
                    itm.setExpanded(True)
                    self.blockSignals(False)
                else:
                    self.expandItem(itm)
        self.openItems = openItems[:]
            
        if self.current:
            citm = self.__findItem(self.curpathlist, 0)
            if citm:
                self.setCurrentItem(citm)
                citm.setSelected(True)
                if self.__scrollToItem:
                    self.scrollToItem(self.__scrollToItem,
                                      QAbstractItemView.PositionAtTop)
                else:
                    self.scrollToItem(citm, QAbstractItemView.PositionAtTop)
                self.current = None
        elif self.__scrollToItem:
            self.scrollToItem(self.__scrollToItem,
                              QAbstractItemView.PositionAtTop)
        
        self.resortEnabled = resortEnabled
        self.__resort()

    def __generateItem(self, parent, dvar, dvalue, dtype, isSpecial=False):
        """
        Private method used to generate a VariableItem.
        
        @param parent parent of the item to be generated
        @param dvar variable name (string)
        @param dvalue value string (string)
        @param dtype type string (string)
        @param isSpecial flag indicating that a special node should be
            generated (boolean)
        @return The item that was generated (VariableItem).
        """
        if isSpecial and \
           (self.dvar_rx_class1.exactMatch(dvar) or
                self.dvar_rx_class2.exactMatch(dvar)):
            isSpecial = False
        
        if self.rx_class2.exactMatch(dtype):
            return SpecialVarItem(parent, dvar, dvalue, dtype[7:-1],
                                  self.framenr, self.scope)
        elif dtype != "void *" and \
            (self.rx_class.exactMatch(dvalue) or
             self.rx_class3.exactMatch(dvalue) or
             isSpecial):
            if self.dvar_rx_special_array_element.exactMatch(dvar):
                return SpecialArrayElementVarItem(parent, dvar, dvalue, dtype,
                                                  self.framenr, self.scope)
            else:
                return SpecialVarItem(parent, dvar, dvalue, dtype,
                                      self.framenr, self.scope)
        else:
            if self.dvar_rx_array_element.exactMatch(dvar):
                return ArrayElementVarItem(parent, dvar, dvalue, dtype)
            else:
                return VariableItem(parent, dvar, dvalue, dtype)
        
    def __addItem(self, parent, vtype, var, value):
        """
        Private method used to add an item to the list.
        
        If the item is of a type with subelements (i.e. list, dictionary,
        tuple), these subelements are added by calling this method recursively.
        
        @param parent the parent of the item to be added
            (QTreeWidgetItem or None)
        @param vtype the type of the item to be added
            (string)
        @param var the variable name (string)
        @param value the value string (string)
        @return The item that was added to the listview (QTreeWidgetItem).
        """
        if parent is None:
            parent = self
        try:
            dvar = '{0}{1}'.format(var, self.indicators[vtype])
        except KeyError:
            dvar = var
        dvtype = self.__getDispType(vtype)
        
        if vtype in ['list', 'Array', 'tuple', 'dict', 'Hash']:
            itm = self.__generateItem(parent, dvar,
                                      self.tr("{0} items").format(value),
                                      dvtype, True)
        elif vtype in ['unicode', 'str']:
            if self.rx_nonprintable.indexIn(value) != -1:
                sval = value
            else:
                try:
                    sval = eval(value)
                except:
                    sval = value
            itm = self.__generateItem(parent, dvar, str(sval), dvtype)
        
        else:
            itm = self.__generateItem(parent, dvar, value, dvtype)
            
        return itm

    def __getDispType(self, vtype):
        """
        Private method used to get the display string for type vtype.
        
        @param vtype the type, the display string should be looked up for
              (string)
        @return displaystring (string)
        """
        try:
            i = ConfigVarTypeStrings.index(vtype)
            dvtype = self.tr(ConfigVarTypeDispStrings[i])
        except ValueError:
            if vtype == 'classobj':
                dvtype = self.tr(ConfigVarTypeDispStrings[
                    ConfigVarTypeStrings.index('instance')])
            else:
                dvtype = vtype
        return dvtype

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Protected method of QAbstractItemView.
        
        Reimplemented to disable expanding/collapsing of items when
        double-clicking. Instead the double-clicked entry is opened.
        
        @param mouseEvent the mouse event object (QMouseEvent)
        """
        itm = self.itemAt(mouseEvent.pos())
        self.__showVariableDetails(itm)
        
    def __showDetails(self):
        """
        Private slot to show details about the selected variable.
        """
        itm = self.currentItem()
        self.__showVariableDetails(itm)
        
    def __showVariableDetails(self, itm):
        """
        Private method to show details about a variable.
        
        @param itm reference to the variable item
        """
        if itm is None:
            return
        
        val = itm.getValue()
        
        if not val:
            return  # do not display anything, if the variable has no value
            
        vtype = itm.text(2)
        name = itm.text(0)
        if name[-2:] in ['[]', '{}', '()']:
            name = name[:-2]
        
        par = itm.parent()
        nlist = [name]
        # build up the fully qualified name
        while par is not None:
            pname = par.text(0)
            if pname[-2:] in ['[]', '{}', '()']:
                if nlist[0].endswith("."):
                    nlist[0] = '[{0}].'.format(nlist[0][:-1])
                else:
                    nlist[0] = '[{0}]'.format(nlist[0])
                nlist.insert(0, pname[:-2])
            else:
                nlist.insert(0, '{0}.'.format(pname))
            par = par.parent()
            
        name = ''.join(nlist)
        # now show the dialog
        from .VariableDetailDialog import VariableDetailDialog
        dlg = VariableDetailDialog(name, vtype, val)
        dlg.exec_()
    
    def __buildTreePath(self, itm):
        """
        Private method to build up a path from the top to an item.
        
        @param itm item to build the path for (QTreeWidgetItem)
        @return list of names denoting the path from the top (list of strings)
        """
        name = itm.text(0)
        pathlist = [name]
        
        par = itm.parent()
        # build up a path from the top to the item
        while par is not None:
            pname = par.text(0)
            pathlist.insert(0, pname)
            par = par.parent()
        
        return pathlist[:]
    
    def __expandItemSignal(self, parentItem):
        """
        Private slot to handle the expanded signal.
        
        @param parentItem reference to the item being expanded
            (QTreeWidgetItem)
        """
        self.expandItem(parentItem)
        self.__scrollToItem = parentItem
        
    def expandItem(self, parentItem):
        """
        Public slot to handle the expanded signal.
        
        @param parentItem reference to the item being expanded
            (QTreeWidgetItem)
        """
        pathlist = self.__buildTreePath(parentItem)
        self.openItems.append(pathlist)
        if parentItem.populated:
            return
        
        try:
            parentItem.expand()
            self.__resort()
        except AttributeError:
            super(VariablesViewer, self).expandItem(parentItem)

    def collapseItem(self, parentItem):
        """
        Public slot to handle the collapsed signal.
        
        @param parentItem reference to the item being collapsed
            (QTreeWidgetItem)
        """
        pathlist = self.__buildTreePath(parentItem)
        self.openItems.remove(pathlist)
        
        try:
            parentItem.collapse()
        except AttributeError:
            super(VariablesViewer, self).collapseItem(parentItem)

    def __resort(self):
        """
        Private method to resort the tree.
        """
        if self.resortEnabled:
            self.sortItems(self.sortColumn(),
                           self.header().sortIndicatorOrder())
    
    def handleResetUI(self):
        """
        Public method to reset the VariablesViewer.
        """
        self.clear()
        self.openItems = []
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface")\
            .showPreferences("debuggerGeneralPage")
