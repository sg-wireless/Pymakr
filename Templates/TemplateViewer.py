# -*- coding: utf-8 -*-

# Copyright (c) 2005 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a template viewer and associated classes.
"""

from __future__ import unicode_literals

import datetime
import os
import re

from PyQt5.QtCore import QFile, QFileInfo, QIODevice, Qt, QCoreApplication
from PyQt5.QtWidgets import QTreeWidget, QDialog, QApplication, QMenu, \
    QTreeWidgetItem

from E5Gui.E5Application import e5App
from E5Gui import E5MessageBox, E5FileDialog

import Preferences

import UI.PixmapCache
import Utilities


class TemplateGroup(QTreeWidgetItem):
    """
    Class implementing a template group.
    """
    def __init__(self, parent, name, language="All"):
        """
        Constructor
        
        @param parent parent widget of the template group (QWidget)
        @param name name of the group (string)
        @param language programming language for the group (string)
        """
        self.name = name
        self.language = language
        self.entries = {}
        
        super(TemplateGroup, self).__init__(parent, [name])
        
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, language)
    
    def setName(self, name):
        """
        Public method to update the name of the group.
        
        @param name name of the group (string)
        """
        self.name = name
        self.setText(0, name)

    def getName(self):
        """
        Public method to get the name of the group.
        
        @return name of the group (string)
        """
        return self.name
        
    def setLanguage(self, language):
        """
        Public method to update the name of the group.
        
        @param language programming language for the group (string)
        """
        self.language = language
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, language)

    def getLanguage(self):
        """
        Public method to get the name of the group.
        
        @return language of the group (string)
        """
        return self.language
        
    def addEntry(self, name, description, template, quiet=False):
        """
        Public method to add a template entry to this group.
        
        @param name name of the entry (string)
        @param description description of the entry to add (string)
        @param template template text of the entry (string)
        @param quiet flag indicating quiet operation (boolean)
        """
        if name in self.entries:
            if not quiet:
                E5MessageBox.critical(
                    None,
                    QCoreApplication.translate("TemplateGroup",
                                               "Add Template"),
                    QCoreApplication.translate(
                        "TemplateGroup",
                        """<p>The group <b>{0}</b> already contains a"""
                        """ template named <b>{1}</b>.</p>""")
                    .format(self.name, name))
            return
        
        self.entries[name] = TemplateEntry(self, name, description, template)
        
        if Preferences.getTemplates("AutoOpenGroups") and \
                not self.isExpanded():
            self.setExpanded(True)
    
    def removeEntry(self, name):
        """
        Public method to remove a template entry from this group.
        
        @param name name of the entry to be removed (string)
        """
        if name in self.entries:
            index = self.indexOfChild(self.entries[name])
            self.takeChild(index)
            del self.entries[name]
            
            if len(self.entries) == 0:
                if Preferences.getTemplates("AutoOpenGroups") and \
                        self.isExpanded():
                    self.setExpanded(False)
    
    def removeAllEntries(self):
        """
        Public method to remove all template entries of this group.
        """
        for name in list(self.entries.keys())[:]:
            self.removeEntry(name)

    def hasEntry(self, name):
        """
        Public method to check, if the group has an entry with the given name.
        
        @param name name of the entry to check for (string)
        @return flag indicating existence (boolean)
        """
        return name in self.entries
    
    def getEntry(self, name):
        """
        Public method to get an entry.
        
        @param name name of the entry to retrieve (string)
        @return reference to the entry (TemplateEntry)
        """
        try:
            return self.entries[name]
        except KeyError:
            return None

    def getEntryNames(self, beginning):
        """
        Public method to get the names of all entries, who's name starts with
        the given string.
        
        @param beginning string denoting the beginning of the template name
            (string)
        @return list of entry names found (list of strings)
        """
        names = []
        for name in self.entries:
            if name.startswith(beginning):
                names.append(name)
        
        return names

    def getAllEntries(self):
        """
        Public method to retrieve all entries.
        
        @return list of all entries (list of TemplateEntry)
        """
        return list(self.entries.values())


class TemplateEntry(QTreeWidgetItem):
    """
    Class immplementing a template entry.
    """
    def __init__(self, parent, name, description, templateText):
        """
        Constructor
        
        @param parent parent widget of the template entry (QWidget)
        @param name name of the entry (string)
        @param description descriptive text for the template (string)
        @param templateText text of the template entry (string)
        """
        self.name = name
        self.description = description
        self.template = templateText
        self.__extractVariables()
        
        super(TemplateEntry, self).__init__(parent, [self.__displayText()])
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, self.template)

    def __displayText(self):
        """
        Private method to generate the display text.
        
        @return display text (string)
        """
        if self.description:
            txt = "{0} - {1}".format(self.name, self.description)
        else:
            txt = self.name
        return txt
    
    def setName(self, name):
        """
        Public method to update the name of the entry.
        
        @param name name of the entry (string)
        """
        self.name = name
        self.setText(0, self.__displayText())

    def getName(self):
        """
        Public method to get the name of the entry.
        
        @return name of the entry (string)
        """
        return self.name

    def setDescription(self, description):
        """
        Public method to update the description of the entry.
        
        @param description description of the entry (string)
        """
        self.description = description
        self.setText(0, self.__displayText())

    def getDescription(self):
        """
        Public method to get the description of the entry.
        
        @return description of the entry (string)
        """
        return self.description

    def getGroupName(self):
        """
        Public method to get the name of the group this entry belongs to.
        
        @return name of the group containing this entry (string)
        """
        return self.parent().getName()
        
    def setTemplateText(self, templateText):
        """
        Public method to update the template text.
        
        @param templateText text of the template entry (string)
        """
        self.template = templateText
        self.__extractVariables()
        if Preferences.getTemplates("ShowTooltip"):
            self.setToolTip(0, self.template)

    def getTemplateText(self):
        """
        Public method to get the template text.
        
        @return the template text (string)
        """
        return self.template

    def getExpandedText(self, varDict, indent):
        """
        Public method to get the template text with all variables expanded.
        
        @param varDict dictionary containing the texts of each variable
            with the variable name as key.
        @param indent indentation of the line receiving he expanded
            template text (string)
        @return a tuple of the expanded template text (string), the
            number of lines (integer) and the length of the last line (integer)
        """
        txt = self.template
        for var, val in list(varDict.items()):
            if var in self.formatedVariables:
                txt = self.__expandFormattedVariable(var, val, txt)
            else:
                txt = txt.replace(var, val)
        sepchar = Preferences.getTemplates("SeparatorChar")
        txt = txt.replace("{0}{1}".format(sepchar, sepchar), sepchar)
        prefix = "{0}{1}".format(os.linesep, indent)
        trailingEol = txt.endswith(os.linesep)
        lines = txt.splitlines()
        lineCount = len(lines)
        lineLen = len(lines[-1])
        txt = prefix.join(lines).lstrip()
        if trailingEol:
            txt = "{0}{1}".format(txt, os.linesep)
            lineCount += 1
            lineLen = 0
        return txt, lineCount, lineLen

    def __expandFormattedVariable(self, var, val, txt):
        """
        Private method to expand a template variable with special formatting.
        
        @param var template variable name (string)
        @param val value of the template variable (string)
        @param txt template text (string)
        @return expanded and formatted variable (string)
        """
        t = ""
        for line in txt.splitlines():
            ind = line.find(var)
            if ind >= 0:
                format = var[1:-1].split(':', 1)[1]
                if format == 'rl':
                    prefix = line[:ind]
                    postfix = line[ind + len(var):]
                    for v in val.splitlines():
                        t = "{0}{1}{2}{3}{4}".format(
                            t, os.linesep, prefix, v, postfix)
                elif format == 'ml':
                    indent = line.replace(line.lstrip(), "")
                    prefix = line[:ind]
                    postfix = line[ind + len(var):]
                    count = 0
                    for v in val.splitlines():
                        if count:
                            t = "{0}{1}{2}{3}".format(t, os.linesep, indent, v)
                        else:
                            t = "{0}{1}{2}{3}".format(t, os.linesep, prefix, v)
                        count += 1
                    t = "{0}{1}".format(t, postfix)
                else:
                    t = "{0}{1}{2}".format(t, os.linesep, line)
            else:
                t = "{0}{1}{2}".format(t, os.linesep, line)
        return "".join(t.splitlines(1)[1:])

    def getVariables(self):
        """
        Public method to get the list of variables.
        
        @return list of variables (list of strings)
        """
        return self.variables

    def __extractVariables(self):
        """
        Private method to retrieve the list of variables.
        """
        sepchar = Preferences.getTemplates("SeparatorChar")
        variablesPattern = \
            re.compile(
                r"""\{0}[a-zA-Z][a-zA-Z0-9_]*(?::(?:ml|rl))?\{1}""".format(
                    sepchar, sepchar))
        variables = variablesPattern.findall(self.template)
        self.variables = []
        self.formatedVariables = []
        for var in variables:
            if var not in self.variables:
                self.variables.append(var)
            if var.find(':') >= 0 and var not in self.formatedVariables:
                self.formatedVariables.append(var)


class TemplateViewer(QTreeWidget):
    """
    Class implementing the template viewer.
    """
    def __init__(self, parent, viewmanager):
        """
        Constructor
        
        @param parent the parent (QWidget)
        @param viewmanager reference to the viewmanager object
        """
        super(TemplateViewer, self).__init__(parent)
        
        self.viewmanager = viewmanager
        self.groups = {}
        
        self.setHeaderLabels(["Template"])
        self.header().hide()
        self.header().setSortIndicator(0, Qt.AscendingOrder)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        
        self.__menu = QMenu(self)
        self.applyAct = self.__menu.addAction(
            self.tr("Apply"), self.__templateItemActivated)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Add entry..."), self.__addEntry)
        self.__menu.addAction(self.tr("Add group..."), self.__addGroup)
        self.__menu.addAction(self.tr("Edit..."), self.__edit)
        self.__menu.addAction(self.tr("Remove"), self.__remove)
        self.__menu.addSeparator()
        self.saveAct = self.__menu.addAction(self.tr("Save"), self.save)
        self.__menu.addAction(self.tr("Import..."), self.__import)
        self.__menu.addAction(self.tr("Export..."), self.__export)
        self.__menu.addAction(self.tr("Reload"), self.__reload)
        self.__menu.addSeparator()
        self.__menu.addAction(
            self.tr("Help about Templates..."), self.__showHelp)
        self.__menu.addSeparator()
        self.__menu.addAction(self.tr("Configure..."), self.__configure)
        
        self.__backMenu = QMenu(self)
        self.__backMenu.addAction(self.tr("Add group..."), self.__addGroup)
        self.__backMenu.addSeparator()
        self.bmSaveAct = self.__backMenu.addAction(self.tr("Save"), self.save)
        self.__backMenu.addAction(self.tr("Import..."), self.__import)
        self.bmExportAct = self.__backMenu.addAction(
            self.tr("Export..."), self.__export)
        self.__backMenu.addAction(self.tr("Reload"), self.__reload)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(
            self.tr("Help about Templates..."), self.__showHelp)
        self.__backMenu.addSeparator()
        self.__backMenu.addAction(
            self.tr("Configure..."), self.__configure)
        
        self.__activating = False
        self.__dirty = False
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.itemActivated.connect(self.__templateItemActivated)
        
        self.setWindowIcon(UI.PixmapCache.getIcon("eric.png"))
        
    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.sortItems(self.sortColumn(), self.header().sortIndicatorOrder())
        
    def __templateItemActivated(self, itm=None, col=0):
        """
        Private slot to handle the activation of an item.
        
        @param itm reference to the activated item (QTreeWidgetItem)
        @param col column the item was activated in (integer)
        """
        if not self.__activating:
            self.__activating = True
            itm = self.currentItem()
            if isinstance(itm, TemplateEntry):
                self.applyTemplate(itm)
            self.__activating = False
        
    def __showContextMenu(self, coord):
        """
        Private slot to show the context menu of the list.
        
        @param coord the position of the mouse pointer (QPoint)
        """
        itm = self.itemAt(coord)
        coord = self.mapToGlobal(coord)
        if itm is None:
            self.bmSaveAct.setEnabled(self.__dirty)
            self.bmExportAct.setEnabled(self.topLevelItemCount() != 0)
            self.__backMenu.popup(coord)
        else:
            self.applyAct.setEnabled(
                self.viewmanager.activeWindow() is not None and
                isinstance(itm, TemplateEntry))
            self.saveAct.setEnabled(self.__dirty)
            self.__menu.popup(coord)
    
    def __addEntry(self):
        """
        Private slot to handle the Add Entry context menu action.
        """
        itm = self.currentItem()
        if isinstance(itm, TemplateGroup):
            groupName = itm.getName()
        else:
            groupName = itm.getGroupName()
        
        from .TemplatePropertiesDialog import TemplatePropertiesDialog
        dlg = TemplatePropertiesDialog(self)
        dlg.setSelectedGroup(groupName)
        if dlg.exec_() == QDialog.Accepted:
            name, description, groupName, template = dlg.getData()
            self.addEntry(groupName, name, description, template)
            self.__dirty = True
        
    def __addGroup(self):
        """
        Private slot to handle the Add Group context menu action.
        """
        from .TemplatePropertiesDialog import TemplatePropertiesDialog
        dlg = TemplatePropertiesDialog(self, True)
        if dlg.exec_() == QDialog.Accepted:
            name, language = dlg.getData()
            self.addGroup(name, language)
            self.__dirty = True
        
    def __edit(self):
        """
        Private slot to handle the Edit context menu action.
        """
        itm = self.currentItem()
        if isinstance(itm, TemplateEntry):
            editGroup = False
        else:
            editGroup = True
        
        from .TemplatePropertiesDialog import TemplatePropertiesDialog
        dlg = TemplatePropertiesDialog(self, editGroup, itm)
        if dlg.exec_() == QDialog.Accepted:
            if editGroup:
                name, language = dlg.getData()
                self.changeGroup(itm.getName(), name, language)
            else:
                name, description, groupName, template = dlg.getData()
                self.changeEntry(itm, name, groupName, description, template)
            self.__dirty = True
        
    def __remove(self):
        """
        Private slot to handle the Remove context menu action.
        """
        itm = self.currentItem()
        res = E5MessageBox.yesNo(
            self,
            self.tr("Remove Template"),
            self.tr("""<p>Do you really want to remove <b>{0}</b>?</p>""")
            .format(itm.getName()))
        if not res:
            return

        if isinstance(itm, TemplateGroup):
            self.removeGroup(itm)
        else:
            self.removeEntry(itm)
        self.__dirty = True

    def save(self):
        """
        Public slot to save the templates.
        """
        if self.__dirty:
            ok = self.writeTemplates()
            if ok:
                self.__dirty = False

    def __import(self):
        """
        Private slot to handle the Import context menu action.
        """
        fn = E5FileDialog.getOpenFileName(
            self,
            self.tr("Import Templates"),
            "",
            self.tr("Templates Files (*.e4c);; All Files (*)"))
        
        if fn:
            self.readTemplates(fn)
            self.__dirty = True

    def __export(self):
        """
        Private slot to handle the Export context menu action.
        """
        fn, selectedFilter = E5FileDialog.getSaveFileNameAndFilter(
            self,
            self.tr("Export Templates"),
            "",
            self.tr("Templates Files (*.e4c);; All Files (*)"),
            "",
            E5FileDialog.Options(E5FileDialog.DontConfirmOverwrite))
        
        if fn:
            ext = QFileInfo(fn).suffix()
            if not ext:
                ex = selectedFilter.split("(*")[1].split(")")[0]
                if ex:
                    fn += ex
            self.writeTemplates(fn)
    
    def __reload(self):
        """
        Private slot to reload the templates.
        """
        if self.__dirty:
            res = E5MessageBox.yesNo(
                self,
                self.tr("Reload Templates"),
                self.tr(
                    """The templates contain unsaved changes. Shall these"""
                    """ changes be discarded?"""),
                icon=E5MessageBox.Warning)
            if not res:
                return
        
        self.clear()
        self.groups = {}
        
        self.readTemplates()
    
    def __showHelp(self):
        """
        Private method to show some help.
        """
        E5MessageBox.information(
            self,
            self.tr("Template Help"),
            self.tr(
                """<p><b>Template groups</b> are a means of grouping"""
                """ individual templates. Groups have an attribute that"""
                """ specifies, which programming language they apply for."""
                """ In order to add template entries, at least one group"""
                """ has to be defined.</p>"""
                """<p><b>Template entries</b> are the actual templates."""
                """ They are grouped by the template groups. Help about"""
                """ how to define them is available in the template edit"""
                """ dialog.</p>"""))

    def __getPredefinedVars(self):
        """
        Private method to return predefined variables.
        
        @return dictionary of predefined variables and their values
        """
        project = e5App().getObject("Project")
        editor = self.viewmanager.activeWindow()
        today = datetime.datetime.now().date()
        sepchar = Preferences.getTemplates("SeparatorChar")
        keyfmt = sepchar + "{0}" + sepchar
        varValues = {keyfmt.format('date'): today.isoformat(),
                     keyfmt.format('year'): str(today.year)}

        if project.name:
            varValues[keyfmt.format('project_name')] = project.name

        if project.ppath:
            varValues[keyfmt.format('project_path')] = project.ppath

        path_name = editor.getFileName()
        if path_name:
            dir_name, file_name = os.path.split(path_name)
            base_name, ext = os.path.splitext(file_name)
            if ext:
                ext = ext[1:]
            varValues.update({
                keyfmt.format('path_name'): path_name,
                keyfmt.format('dir_name'): dir_name,
                keyfmt.format('file_name'): file_name,
                keyfmt.format('base_name'): base_name,
                keyfmt.format('ext'): ext
            })
        
        varValues[keyfmt.format('clipboard:ml')] = \
            QApplication.clipboard().text()
        varValues[keyfmt.format('clipboard')] = \
            QApplication.clipboard().text()

        if editor.hasSelectedText():
            varValues[keyfmt.format('cur_select:ml')] = editor.selectedText()
            varValues[keyfmt.format('cur_select')] = editor.selectedText()
        else:
            varValues[keyfmt.format('cur_select:ml')] = os.linesep
            varValues[keyfmt.format('cur_select')] = ""

        varValues[keyfmt.format('insertion')] = "i_n_s_e_r_t_i_o_n"
        
        varValues[keyfmt.format('select_start')] = "s_e_l_e_c_t_s_t_a_r_t"
        varValues[keyfmt.format('select_end')] = "s_e_l_e_c_t_e_n_d"

        return varValues

    def applyTemplate(self, itm):
        """
        Public method to apply the template.
        
        @param itm reference to the template item to apply (TemplateEntry)
        """
        editor = self.viewmanager.activeWindow()
        if editor is None:
            return
        
        ok = False
        vars = itm.getVariables()
        varValues = self.__getPredefinedVars()
        
        # Remove predefined variables from list so user doesn't have to fill
        # these values out in the dialog.
        for v in list(varValues.keys()):
            if v in vars:
                vars.remove(v)
        
        if vars:
            if Preferences.getTemplates("SingleDialog"):
                from .TemplateMultipleVariablesDialog import \
                    TemplateMultipleVariablesDialog
                dlg = TemplateMultipleVariablesDialog(vars, self)
                if dlg.exec_() == QDialog.Accepted:
                    varValues.update(dlg.getVariables())
                    ok = True
            else:
                from .TemplateSingleVariableDialog import \
                    TemplateSingleVariableDialog
                for var in vars:
                    dlg = TemplateSingleVariableDialog(var, self)
                    if dlg.exec_() == QDialog.Accepted:
                        varValues[var] = dlg.getVariable()
                    else:
                        return
                    del dlg
                ok = True
        else:
            ok = True
        
        if ok:
            line = editor.text(editor.getCursorPosition()[0])\
                .replace(os.linesep, "")
            indent = line.replace(line.lstrip(), "")
            txt, lines, count = itm.getExpandedText(varValues, indent)
            # It should be done in this way to allow undo
            editor.beginUndoAction()
            if editor.hasSelectedText():
                line, index = editor.getSelection()[0:2]
                editor.removeSelectedText()
            else:
                line, index = editor.getCursorPosition()
            
            if lines == 1:
                count += index
            else:
                if len(indent) > 0:
                    count += len(indent)
            
            if "i_n_s_e_r_t_i_o_n" in txt and "s_e_l_e_c_t" in txt:
                txt = "'Insertion and selection can not be in" \
                    " template together'"
            
            if "i_n_s_e_r_t_i_o_n" in txt:
                lines = 1
                for aline in txt.splitlines():
                    count = aline.find("i_n_s_e_r_t_i_o_n")
                    if count >= 0:
                        txt = txt.replace("i_n_s_e_r_t_i_o_n", "")
                        if lines == 1:
                            count += index
                        else:
                            if len(indent) > 0:
                                count += len(indent)
                        break
                    else:
                        lines += 1
            
            setselect = False
            if "s_e_l_e_c_t_s_t_a_r_t" in txt and "s_e_l_e_c_t_e_n_d" in txt:
                setselect = True
                linea = 1
                for aline in txt.splitlines():
                    posa = aline.find("s_e_l_e_c_t_s_t_a_r_t")
                    if posa >= 0:
                        txt = txt.replace("s_e_l_e_c_t_s_t_a_r_t", "")
                        break
                    else:
                        linea += 1
                lineb = 1
                for aline in txt.splitlines():
                    posb = aline.find("s_e_l_e_c_t_e_n_d")
                    if posb >= 0:
                        txt = txt.replace("s_e_l_e_c_t_e_n_d", "")
                        break
                    else:
                        lineb += 1
            
            editor.insert(txt)
            
            if setselect:
                editor.setSelection(line + linea - 1, posa,
                                    line + lineb - 1, posb)
            else:
                editor.setCursorPosition(line + lines - 1, count)
                
            editor.endUndoAction()
            editor.setFocus()

    def applyNamedTemplate(self, templateName, groupName=None):
        """
        Public method to apply a template given a template name.
        
        @param templateName name of the template item to apply (string)
        @param groupName name of the group to get the entry from (string).
            None or empty means to apply the first template found with the
            given name.
        """
        if groupName:
            if self.hasGroup(groupName):
                groups = [self.groups[groupName]]
            else:
                return
        else:
            groups = list(self.groups.values())
        for group in groups:
            template = group.getEntry(templateName)
            if template is not None:
                self.applyTemplate(template)
                break
    
    def addEntry(self, groupName, name, description, template, quiet=False):
        """
        Public method to add a template entry.
        
        @param groupName name of the group to add to (string)
        @param name name of the entry to add (string)
        @param description description of the entry to add (string)
        @param template template text of the entry (string)
        @param quiet flag indicating quiet operation (boolean)
        """
        self.groups[groupName].addEntry(
            name, description, template, quiet=quiet)
        self.__resort()
    
    def hasGroup(self, name):
        """
        Public method to check, if a group with the given name exists.
        
        @param name name of the group to be checked for (string)
        @return flag indicating an existing group (boolean)
        """
        return name in self.groups
    
    def addGroup(self, name, language="All"):
        """
        Public method to add a group.
        
        @param name name of the group to be added (string)
        @param language programming language for the group (string)
        """
        if name not in self.groups:
            self.groups[name] = TemplateGroup(self, name, language)
        self.__resort()

    def changeGroup(self, oldname, newname, language="All"):
        """
        Public method to rename a group.
        
        @param oldname old name of the group (string)
        @param newname new name of the group (string)
        @param language programming language for the group (string)
        """
        if oldname != newname:
            if newname in self.groups:
                E5MessageBox.warning(
                    self,
                    self.tr("Edit Template Group"),
                    self.tr("""<p>A template group with the name"""
                            """ <b>{0}</b> already exists.</p>""")
                    .format(newname))
                return
            
            self.groups[newname] = self.groups[oldname]
            del self.groups[oldname]
            self.groups[newname].setName(newname)
        
        self.groups[newname].setLanguage(language)
        self.__resort()

    def getAllGroups(self):
        """
        Public method to get all groups.
        
        @return list of all groups (list of TemplateGroup)
        """
        return list(self.groups.values())
    
    def getGroupNames(self):
        """
        Public method to get all group names.
        
        @return list of all group names (list of strings)
        """
        groups = sorted(list(self.groups.keys())[:])
        return groups

    def removeGroup(self, itm):
        """
        Public method to remove a group.
        
        @param itm template group to be removed (TemplateGroup)
        """
        name = itm.getName()
        itm.removeAllEntries()
        index = self.indexOfTopLevelItem(itm)
        self.takeTopLevelItem(index)
        del self.groups[name]

    def removeEntry(self, itm):
        """
        Public method to remove a template entry.
        
        @param itm template entry to be removed (TemplateEntry)
        """
        groupName = itm.getGroupName()
        self.groups[groupName].removeEntry(itm.getName())

    def changeEntry(self, itm, name, groupName, description, template):
        """
        Public method to change a template entry.
        
        @param itm template entry to be changed (TemplateEntry)
        @param name new name for the entry (string)
        @param groupName name of the group the entry should belong to
            (string)
        @param description description of the entry (string)
        @param template template text of the entry (string)
        """
        if itm.getGroupName() != groupName:
            # move entry to another group
            self.groups[itm.getGroupName()].removeEntry(itm.getName())
            self.groups[groupName].addEntry(name, description, template)
            return
        
        if itm.getName() != name:
            # entry was renamed
            self.groups[groupName].removeEntry(itm.getName())
            self.groups[groupName].addEntry(name, description, template)
            return
        
        tmpl = self.groups[groupName].getEntry(name)
        tmpl.setDescription(description)
        tmpl.setTemplateText(template)
        self.__resort()

    def writeTemplates(self, filename=None):
        """
        Public method to write the templates data to an XML file (.e4c).
        
        @param filename name of a templates file to read (string)
        @return flag indicating success (boolean)
        """
        if filename is None:
            filename = os.path.join(
                Utilities.getConfigDir(), "eric6templates.e4c")
        f = QFile(filename)
        ok = f.open(QIODevice.WriteOnly)
        if not ok:
            E5MessageBox.critical(
                self,
                self.tr("Save templates"),
                self.tr(
                    "<p>The templates file <b>{0}</b> could not be"
                    " written.</p>")
                .format(filename))
            return False
        
        from E5XML.TemplatesWriter import TemplatesWriter
        TemplatesWriter(f, self).writeXML()
        f.close()
        
        return True
    
    def readTemplates(self, filename=None):
        """
        Public method to read in the templates file (.e4c).
        
        @param filename name of a templates file to read (string)
        """
        if filename is None:
            filename = os.path.join(
                Utilities.getConfigDir(), "eric6templates.e4c")
            if not os.path.exists(filename):
                return
        
        f = QFile(filename)
        if f.open(QIODevice.ReadOnly):
            from E5XML.TemplatesReader import TemplatesReader
            reader = TemplatesReader(f, viewer=self)
            reader.readXML()
            f.close()
        else:
            E5MessageBox.critical(
                self,
                self.tr("Read templates"),
                self.tr(
                    "<p>The templates file <b>{0}</b> could not be read.</p>")
                .format(filename))
    
    def __configure(self):
        """
        Private method to open the configuration dialog.
        """
        e5App().getObject("UserInterface").showPreferences("templatesPage")
    
    def hasTemplate(self, entryName, groupName=None):
        """
        Public method to check, if an entry of the given name exists.
        
        @param entryName name of the entry to check for (string)
        @param groupName name of the group to check for the entry (string).
            None or empty means to check all groups.
        @return flag indicating the existence (boolean)
        """
        if groupName:
            if self.hasGroup(groupName):
                groups = [self.groups[groupName]]
            else:
                groups = []
        else:
            groups = list(self.groups.values())
        for group in groups:
            if group.hasEntry(entryName):
                return True
        
        return False
    
    def getTemplateNames(self, start, groupName=None):
        """
        Public method to get the names of templates starting with the
        given string.
        
        @param start start string of the name (string)
        @param groupName name of the group to get the entry from (string).
            None or empty means to look in all groups.
        @return sorted list of matching template names (list of strings)
        """
        names = []
        if groupName:
            if self.hasGroup(groupName):
                groups = [self.groups[groupName]]
            else:
                groups = []
        else:
            groups = list(self.groups.values())
        for group in groups:
            names.extend(group.getEntryNames(start))
        return sorted(names)
