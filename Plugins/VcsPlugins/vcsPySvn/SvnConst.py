# -*- coding: utf-8 -*-

# Copyright (c) 2006 - 2015 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing some constants for the pysvn package.
"""

from __future__ import unicode_literals

from PyQt5.QtCore import QT_TRANSLATE_NOOP

import pysvn

svnNotifyActionMap = {
    pysvn.wc_notify_action.add:
    QT_TRANSLATE_NOOP('Subversion', 'Add'),
    pysvn.wc_notify_action.commit_added:
    QT_TRANSLATE_NOOP('Subversion', 'Add'),
    pysvn.wc_notify_action.commit_deleted:
    QT_TRANSLATE_NOOP('Subversion', 'Delete'),
    pysvn.wc_notify_action.commit_modified:
    QT_TRANSLATE_NOOP('Subversion', 'Modify'),
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced:
    QT_TRANSLATE_NOOP('Subversion', 'Replace'),
    pysvn.wc_notify_action.copy:
    QT_TRANSLATE_NOOP('Subversion', 'Copy'),
    pysvn.wc_notify_action.delete:
    QT_TRANSLATE_NOOP('Subversion', 'Delete'),
    pysvn.wc_notify_action.failed_revert:
    QT_TRANSLATE_NOOP('Subversion', 'Failed revert'),
    pysvn.wc_notify_action.resolved:
    QT_TRANSLATE_NOOP('Subversion', 'Resolve'),
    pysvn.wc_notify_action.restore:
    QT_TRANSLATE_NOOP('Subversion', 'Restore'),
    pysvn.wc_notify_action.revert:
    QT_TRANSLATE_NOOP('Subversion', 'Revert'),
    pysvn.wc_notify_action.skip:
    QT_TRANSLATE_NOOP('Subversion', 'Skip'),
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external:
    QT_TRANSLATE_NOOP('Subversion', 'External'),
    pysvn.wc_notify_action.update_add:
    QT_TRANSLATE_NOOP('Subversion', 'Add'),
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete:
    QT_TRANSLATE_NOOP('Subversion', 'Delete'),
    pysvn.wc_notify_action.update_external:
    QT_TRANSLATE_NOOP('Subversion', 'External'),
    pysvn.wc_notify_action.update_update:
    QT_TRANSLATE_NOOP('Subversion', 'Update'),
    pysvn.wc_notify_action.annotate_revision:
    QT_TRANSLATE_NOOP('Subversion', 'Annotate'),
}
if hasattr(pysvn.wc_notify_action, 'locked'):
    svnNotifyActionMap[pysvn.wc_notify_action.locked] = \
        QT_TRANSLATE_NOOP('Subversion', 'Locking')
    svnNotifyActionMap[pysvn.wc_notify_action.unlocked] = \
        QT_TRANSLATE_NOOP('Subversion', 'Unlocking')
    svnNotifyActionMap[pysvn.wc_notify_action.failed_lock] = \
        QT_TRANSLATE_NOOP('Subversion', 'Failed lock')
    svnNotifyActionMap[pysvn.wc_notify_action.failed_unlock] = \
        QT_TRANSLATE_NOOP('Subversion', 'Failed unlock')
if hasattr(pysvn.wc_notify_action, 'changelist_clear'):
    svnNotifyActionMap[pysvn.wc_notify_action.changelist_clear] = \
        QT_TRANSLATE_NOOP('Subversion', 'Changelist clear')
    svnNotifyActionMap[pysvn.wc_notify_action.changelist_set] = \
        QT_TRANSLATE_NOOP('Subversion', 'Changelist set')
    svnNotifyActionMap[pysvn.wc_notify_action.changelist_moved] = \
        QT_TRANSLATE_NOOP('Subversion', 'Changelist moved')

svnStatusMap = {
    pysvn.wc_status_kind.added:
    QT_TRANSLATE_NOOP('Subversion', 'added'),
    pysvn.wc_status_kind.conflicted:
    QT_TRANSLATE_NOOP('Subversion', 'conflict'),
    pysvn.wc_status_kind.deleted:
    QT_TRANSLATE_NOOP('Subversion', 'deleted'),
    pysvn.wc_status_kind.external:
    QT_TRANSLATE_NOOP('Subversion', 'external'),
    pysvn.wc_status_kind.ignored:
    QT_TRANSLATE_NOOP('Subversion', 'ignored'),
    pysvn.wc_status_kind.incomplete:
    QT_TRANSLATE_NOOP('Subversion', 'incomplete'),
    pysvn.wc_status_kind.missing:
    QT_TRANSLATE_NOOP('Subversion', 'missing'),
    pysvn.wc_status_kind.merged:
    QT_TRANSLATE_NOOP('Subversion', 'merged'),
    pysvn.wc_status_kind.modified:
    QT_TRANSLATE_NOOP('Subversion', 'modified'),
    pysvn.wc_status_kind.none:
    QT_TRANSLATE_NOOP('Subversion', 'normal'),
    pysvn.wc_status_kind.normal:
    QT_TRANSLATE_NOOP('Subversion', 'normal'),
    pysvn.wc_status_kind.obstructed:
    QT_TRANSLATE_NOOP('Subversion', 'type error'),
    pysvn.wc_status_kind.replaced:
    QT_TRANSLATE_NOOP('Subversion', 'replaced'),
    pysvn.wc_status_kind.unversioned:
    QT_TRANSLATE_NOOP('Subversion', 'unversioned'),
}
