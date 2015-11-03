# -*- coding: utf-8 -*-

# Copyright (c) 2012 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a delegate for the special list widget for GreaseMonkey
scripts.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import Qt, QSize, QRect, qVersion
from PyQt5.QtGui import QFontMetrics, QPalette, QFont
from PyQt5.QtWidgets import QStyle, QStyledItemDelegate, QApplication
if qVersion() >= "5.0.0":
    from PyQt5.QtWidgets import QStyleOptionViewItem
else:
    from PyQt5.QtWidgets import QStyleOptionViewItemV4 as QStyleOptionViewItem

import UI.PixmapCache
import Globals


class GreaseMonkeyConfigurationListDelegate(QStyledItemDelegate):
    """
    Class implementing a delegate for the special list widget for GreaseMonkey
    scripts.
    """
    IconSize = 32
    RemoveIconSize = 16
    CheckBoxSize = 18
    MinPadding = 5
    ItemWidth = 200
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent object (QObject)
        """
        super(GreaseMonkeyConfigurationListDelegate, self).__init__(parent)
        
        self.__removePixmap = \
            UI.PixmapCache.getIcon("greaseMonkeyTrash.png").pixmap(
                GreaseMonkeyConfigurationListDelegate.RemoveIconSize)
        self.__rowHeight = 0
        self.__padding = 0
    
    def padding(self):
        """
        Public method to get the padding used.
        
        @return padding used (integer)
        """
        return self.__padding
    
    def paint(self, painter, option, index):
        """
        Public method to paint the specified list item.
        
        @param painter painter object to paint to (QPainter)
        @param option style option used for painting (QStyleOptionViewItem)
        @param index model index of the item (QModelIndex)
        """
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        height = opt.rect.height()
        center = height // 2 + opt.rect.top()
        
        # Prepare title font
        titleFont = QFont(opt.font)
        titleFont.setBold(True)
        titleFont.setPointSize(titleFont.pointSize() + 1)
        
        titleMetrics = QFontMetrics(titleFont)
        if Globals.isWindowsPlatform():
            colorRole = QPalette.Text
        else:
            colorRole = QPalette.HighlightedText \
                if opt.state & QStyle.State_Selected else QPalette.Text
        
        leftPos = self.__padding
        rightPos = opt.rect.right() - self.__padding - \
            GreaseMonkeyConfigurationListDelegate.RemoveIconSize
        
        # Draw background
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, opt, painter, widget)
        
        # Draw checkbox
        checkBoxYPos = center - \
            GreaseMonkeyConfigurationListDelegate.CheckBoxSize // 2
        opt2 = QStyleOptionViewItem(opt)
        if opt2.checkState == Qt.Checked:
            opt2.state |= QStyle.State_On
        else:
            opt2.state |= QStyle.State_Off
        styleCheckBoxRect = style.subElementRect(
            QStyle.SE_ViewItemCheckIndicator, opt2, widget)
        opt2.rect = QRect(
            leftPos, checkBoxYPos,
            styleCheckBoxRect.width(), styleCheckBoxRect.height())
        style.drawPrimitive(QStyle.PE_IndicatorViewItemCheck, opt2, painter,
                            widget)
        leftPos = opt2.rect.right() + self.__padding
        
        # Draw icon
        iconYPos = center - GreaseMonkeyConfigurationListDelegate.IconSize // 2
        iconRect = QRect(leftPos, iconYPos,
                         GreaseMonkeyConfigurationListDelegate.IconSize,
                         GreaseMonkeyConfigurationListDelegate.IconSize)
        pixmap = index.data(Qt.DecorationRole).pixmap(
            GreaseMonkeyConfigurationListDelegate.IconSize)
        painter.drawPixmap(iconRect, pixmap)
        leftPos = iconRect.right() + self.__padding
        
        # Draw script name
        name = index.data(Qt.DisplayRole)
        leftTitleEdge = leftPos + 2
        rightTitleEdge = rightPos - self.__padding
        leftPosForVersion = titleMetrics.width(name) + self.__padding
        nameRect = QRect(leftTitleEdge, opt.rect.top() + self.__padding,
                         rightTitleEdge - leftTitleEdge, titleMetrics.height())
        painter.setFont(titleFont)
        style.drawItemText(painter, nameRect, Qt.AlignLeft, opt.palette, True,
                           name, colorRole)
        
        # Draw version
        version = index.data(Qt.UserRole)
        versionRect = QRect(
            nameRect.x() + leftPosForVersion, nameRect.y(),
            rightTitleEdge - leftTitleEdge, titleMetrics.height())
        versionFont = titleFont
        painter.setFont(versionFont)
        style.drawItemText(painter, versionRect, Qt.AlignLeft, opt.palette,
                           True, version, colorRole)
        
        # Draw description
        infoYPos = nameRect.bottom() + opt.fontMetrics.leading()
        infoRect = QRect(
            nameRect.x(), infoYPos,
            nameRect.width(), opt.fontMetrics.height())
        info = opt.fontMetrics.elidedText(
            index.data(Qt.UserRole + 1), Qt.ElideRight, infoRect.width())
        painter.setFont(opt.font)
        style.drawItemText(painter, infoRect, Qt.AlignLeft | Qt.TextSingleLine,
                           opt.palette, True, info, colorRole)
        
        # Draw remove button
        removeIconYPos = center - \
            GreaseMonkeyConfigurationListDelegate.RemoveIconSize // 2
        removeIconRect = QRect(
            rightPos, removeIconYPos,
            GreaseMonkeyConfigurationListDelegate.RemoveIconSize,
            GreaseMonkeyConfigurationListDelegate.RemoveIconSize)
        painter.drawPixmap(removeIconRect, self.__removePixmap)
    
    def sizeHint(self, option, index):
        """
        Public method to get a size hint for the specified list item.
        
        @param option style option used for painting (QStyleOptionViewItem)
        @param index model index of the item (QModelIndex)
        @return size hint (QSize)
        """
        if not self.__rowHeight:
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            
            widget = opt.widget
            style = widget.style() if widget is not None \
                else QApplication.style()
            padding = style.pixelMetric(QStyle.PM_FocusFrameHMargin) + 1
            
            titleFont = opt.font
            titleFont.setBold(True)
            titleFont.setPointSize(titleFont.pointSize() + 1)
            
            self.__padding = padding \
                if padding > GreaseMonkeyConfigurationListDelegate.MinPadding \
                else GreaseMonkeyConfigurationListDelegate.MinPadding
            
            titleMetrics = QFontMetrics(titleFont)
            
            self.__rowHeight = 2 * self.__padding + \
                opt.fontMetrics.leading() + \
                opt.fontMetrics.height() + \
                titleMetrics.height()
        
        return QSize(GreaseMonkeyConfigurationListDelegate.ItemWidth,
                     self.__rowHeight)
