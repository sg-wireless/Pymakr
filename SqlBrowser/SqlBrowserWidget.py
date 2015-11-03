# -*- coding: utf-8 -*-

# Copyright (c) 2009 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the SQL Browser widget.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import pyqtSignal, QVariant, Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget, QDialog, QAbstractItemView
from PyQt5.QtSql import QSqlDatabase, QSqlError, QSqlTableModel, \
    QSqlQueryModel, QSqlQuery

from E5Gui import E5MessageBox

from .Ui_SqlBrowserWidget import Ui_SqlBrowserWidget


class SqlBrowserWidget(QWidget, Ui_SqlBrowserWidget):
    """
    Class implementing the SQL Browser widget.
    
    @signal statusMessage(str) emitted to show a status message
    """
    statusMessage = pyqtSignal(str)
    
    cCount = 0
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        """
        super(SqlBrowserWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.table.addAction(self.insertRowAction)
        self.table.addAction(self.deleteRowAction)
        
        if len(QSqlDatabase.drivers()) == 0:
            E5MessageBox.information(
                self,
                self.tr("No database drivers found"),
                self.tr(
                    """This tool requires at least one Qt database driver. """
                    """Please check the Qt documentation how to build the """
                    """Qt SQL plugins."""))
        
        self.connections.tableActivated.connect(
            self.on_connections_tableActivated)
        self.connections.schemaRequested.connect(
            self.on_connections_schemaRequested)
        self.connections.cleared.connect(self.on_connections_cleared)
        
        self.statusMessage.emit(self.tr("Ready"))
    
    @pyqtSlot()
    def on_clearButton_clicked(self):
        """
        Private slot to clear the SQL entry widget.
        """
        self.sqlEdit.clear()
        self.sqlEdit.setFocus()
    
    @pyqtSlot()
    def on_executeButton_clicked(self):
        """
        Private slot to execute the entered SQL query.
        """
        self.executeQuery()
        self.sqlEdit.setFocus()
    
    @pyqtSlot()
    def on_insertRowAction_triggered(self):
        """
        Private slot handling the action to insert a new row.
        """
        self.__insertRow()
    
    @pyqtSlot()
    def on_deleteRowAction_triggered(self):
        """
        Private slot handling the action to delete a row.
        """
        self.__deleteRow()
    
    @pyqtSlot(str)
    def on_connections_tableActivated(self, table):
        """
        Private slot to show the contents of a table.
        
        @param table name of the table for which to show the contents (string)
        """
        self.showTable(table)
    
    @pyqtSlot(str)
    def on_connections_schemaRequested(self, table):
        """
        Private slot to show the schema of a table.
        
        @param table name of the table for which to show the schema (string)
        """
        self.showSchema(table)
    
    @pyqtSlot()
    def on_connections_cleared(self):
        """
        Private slot to clear the table.
        """
        model = QStandardItemModel(self.table)
        self.table.setModel(model)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.updateActions()
    
    def addConnection(self, driver, dbName, user, password, host, port):
        """
        Public method to add a database connection.
        
        @param driver name of the Qt database driver (string)
        @param dbName name of the database (string)
        @param user user name (string)
        @param password password (string)
        @param host host name (string)
        @param port port number (integer)
        @return SQL error object (QSqlError)
        """
        err = QSqlError()
        
        self.__class__.cCount += 1
        db = QSqlDatabase.addDatabase(
            driver.upper(), "Browser{0:d}".format(self.__class__.cCount))
        db.setDatabaseName(dbName)
        db.setHostName(host)
        db.setPort(port)
        if not db.open(user, password):
            err = db.lastError()
            db = QSqlDatabase()
            QSqlDatabase.removeDatabase(
                "Browser{0:d}".format(self.__class__.cCount))
        
        self.connections.refresh()
        
        return err
    
    def addConnectionByDialog(self):
        """
        Public slot to add a database connection via an input dialog.
        """
        from .SqlConnectionDialog import SqlConnectionDialog
        dlg = SqlConnectionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            driver, dbName, user, password, host, port = dlg.getData()
            err = self.addConnection(
                driver, dbName, user, password, host, port)
            
            if err.type() != QSqlError.NoError:
                E5MessageBox.warning(
                    self,
                    self.tr("Unable to open database"),
                    self.tr(
                        """An error occurred while opening the connection."""))
    
    def showTable(self, table):
        """
        Public slot to show the contents of a table.
        
        @param table name of the table to be shown (string)
        """
        model = QSqlTableModel(self.table, self.connections.currentDatabase())
        model.setEditStrategy(QSqlTableModel.OnRowChange)
        model.setTable(table)
        model.select()
        if model.lastError().type() != QSqlError.NoError:
            self.statusMessage.emit(model.lastError().text())
        self.table.setModel(model)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        self.table.resizeColumnsToContents()
        
        self.table.selectionModel().currentRowChanged.connect(
            self.updateActions)
        
        self.updateActions()
    
    def showSchema(self, table):
        """
        Public slot to show the schema of a table.
        
        @param table name of the table to be shown (string)
        """
        rec = self.connections.currentDatabase().record(table)
        model = QStandardItemModel(self.table)
        
        model.insertRows(0, rec.count())
        model.insertColumns(0, 7)
        
        model.setHeaderData(0, Qt.Horizontal, "Fieldname")
        model.setHeaderData(1, Qt.Horizontal, "Type")
        model.setHeaderData(2, Qt.Horizontal, "Length")
        model.setHeaderData(3, Qt.Horizontal, "Precision")
        model.setHeaderData(4, Qt.Horizontal, "Required")
        model.setHeaderData(5, Qt.Horizontal, "Auto Value")
        model.setHeaderData(6, Qt.Horizontal, "Default Value")
        
        for i in range(rec.count()):
            fld = rec.field(i)
            model.setData(model.index(i, 0), fld.name())
            if fld.typeID() == -1:
                model.setData(model.index(i, 1),
                              QVariant.typeToName(fld.type()))
            else:
                model.setData(
                    model.index(i, 1), "{0} ({1})".format(
                        QVariant.typeToName(fld.type()), fld.typeID()))
            if fld.length() < 0:
                model.setData(model.index(i, 2), "?")
            else:
                model.setData(model.index(i, 2), fld.length())
            if fld.precision() < 0:
                model.setData(model.index(i, 3), "?")
            else:
                model.setData(model.index(i, 3), fld.precision())
            if fld.requiredStatus() == -1:
                model.setData(model.index(i, 4), "?")
            else:
                model.setData(model.index(i, 4), bool(fld.requiredStatus()))
            model.setData(model.index(i, 5), fld.isAutoValue())
            model.setData(model.index(i, 6), fld.defaultValue())
        
        self.table.setModel(model)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.table.resizeColumnsToContents()
        
        self.updateActions()
    
    def updateActions(self):
        """
        Public slot to update the actions.
        """
        enableIns = isinstance(self.table.model(), QSqlTableModel)
        enableDel = enableIns & self.table.currentIndex().isValid()
        
        self.insertRowAction.setEnabled(enableIns)
        self.deleteRowAction.setEnabled(enableDel)
    
    def __insertRow(self):
        """
        Private slot to insert a row into the database table.
        """
        model = self.table.model()
        if not isinstance(model, QSqlTableModel):
            return
        
        insertIndex = self.table.currentIndex()
        if insertIndex.row() == -1:
            row = 0
        else:
            row = insertIndex.row()
        model.insertRow(row)
        insertIndex = model.index(row, 0)
        self.table.setCurrentIndex(insertIndex)
        self.table.edit(insertIndex)
    
    def __deleteRow(self):
        """
        Private slot to delete a row from the database table.
        """
        model = self.table.model()
        if not isinstance(model, QSqlTableModel):
            return
        
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        
        currentSelection = self.table.selectionModel().selectedIndexes()
        for selectedIndex in currentSelection:
            if selectedIndex.column() != 0:
                continue
            model.removeRow(selectedIndex.row())
        
        model.submitAll()
        model.setEditStrategy(QSqlTableModel.OnRowChange)
        
        self.updateActions()
    
    def executeQuery(self):
        """
        Public slot to execute the entered query.
        """
        model = QSqlQueryModel(self.table)
        model.setQuery(QSqlQuery(
            self.sqlEdit.toPlainText(), self.connections.currentDatabase()))
        self.table.setModel(model)
        
        if model.lastError().type() != QSqlError.NoError:
            self.statusMessage.emit(model.lastError().text())
        elif model.query().isSelect():
            self.statusMessage.emit(self.tr("Query OK."))
        else:
            self.statusMessage.emit(
                self.tr("Query OK, number of affected rows: {0}")
                    .format(model.query().numRowsAffected()))
        
        self.table.resizeColumnsToContents()
        
        self.updateActions()
