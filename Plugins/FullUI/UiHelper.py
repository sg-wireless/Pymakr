def removeWidgetActions(widget, items):
    """
    Method that removes widget items.

    @param widget QWidget to modify
    @param items list of names of the elements to remove
    """
    for i, item in enumerate(items):
        items[i] = widget.tr(item)

    for item in widget.actions():
        if item.text() in items:
            widget.removeAction(item)

def hideWidgetActions(widget, items):
    """
    Method that hides widget items.

    @param widget QWidget to modify
    @param items list of names of the elements to hide
    """
    for i, item in enumerate(items):
        items[i] = widget.tr(item)

    for item in widget.actions():
        if item.text() in items:
            item.setVisible(False)


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
    ui.getToolbar(toolbar)[1].hide()
    ui.unregisterToolbar(toolbar)

def setToolbarSize(ui, toolbar, size):
    try:
        ui.getToolbar(toolbar)[1].setIconSize(size)
    except:
        pass

def hideItemsSidebar(sidebar, items):
    for el, val in enumerate(items):
        items[el] = sidebar.tr(val)

    for i in range(sidebar.count() - 1, 0, -1):
        if sidebar.tabText(i) in items:
            sidebar.removeTab(i)
