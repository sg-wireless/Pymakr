def removeWidgetActions(widget, items):
    """
    Method that removes widget items.

    @param widget QWidget to modify
    @param items list of names of the elements to remove
    """
    for i, item in enumerate(items):
        items[i] = widget.tr(item)

    for item in widget.actions():
        try:
            if item.text() in items:
                widget.removeAction(item)
        except:
            pass

def hideWidgetActions(widget, items):
    """
    Method that hides widget items.

    @param widget QWidget to modify
    @param items list of names of the elements to hide
    """
    for i, item in enumerate(items):
        items[i] = widget.tr(item)

    for item in widget.actions():
        try:
            if item.text() in items:
                item.setVisible(False)
        except:
            pass


def hideWidgetSeparator(widget, items, mode="after"):
    """
    Method that hides the separator before/after some
    widget items.

    @param widget QWidget to modify
    @param items list of names of the elements right before the separators
    @param where is the separator located
    """
    for i, item in enumerate(items):
        items[i] = widget.tr(item)

    toHide = False
    for item in widget.actions():
        if mode == "after":
            if item.text() == "" and toHide is True:
                item.setVisible(False)
                continue

            if item.text() in items:
                toHide = True
            else:
                toHide = False
        else:
            if item.text() == "":
                prevSeparator = item
            elif item.text() in items and prevSeparator != None:
                prevSeparator.setVisible(False)
            else:
                prevSeparator = None

def hideUnusedMenu(ui, name):
    ui.getMenuBarAction(name).setVisible(False)

def setMenuNonDetachable(ui, name):
    ui.getMenu(name).setTearOffEnabled(False)

def hideToolbar(ui, toolbar):
    try:
        ui.getToolbar(toolbar)[1].hide()
        ui.unregisterToolbar(toolbar)
    except:
        pass

def setToolbarSize(ui, toolbar, size):
    try:
        if ui.getToolbar(toolbar)[1].isVisible():
            ui.getToolbar(toolbar)[1].setIconSize(size)
    except:
        pass

def hideItemsSidebar(sidebar, items):
    for el, val in enumerate(items):
        items[el] = sidebar.tr(val)

    tabCount = sidebar.count()
    for i in range(tabCount, 0, -1):
        if sidebar.tabText(i - 1) in items:
            sidebar.removeTab(i - 1)

def removeTreeTopElements(tree, toDelete):
    childCount = tree.topLevelItemCount()
    for i in range(childCount, 0, -1):
        child = tree.topLevelItem(i - 1)
        if child.text(0) in toDelete:
            tree.takeTopLevelItem(i - 1)

def removeTreeElements(tree, toDelete, name='', level=0):
    if level:
        childCount = tree.childCount()
        for i in range(childCount, 0, -1):
            child = tree.child(i - 1)
            if name + child.text(0) in toDelete:
                tree.takeChild(i - 1)
            else:
                removeTreeElements(child, toDelete, name + child.text(0) + '/', level + 1)

    else:
        childCount = tree.topLevelItemCount()
        for i in range(childCount, 0, -1):
            child = tree.topLevelItem(i - 1)
            if child.text(0) in toDelete:
                tree.takeTopLevelItem(i - 1)
            else:
                removeTreeElements(child, toDelete, child.text(0) + '/', level + 1)
