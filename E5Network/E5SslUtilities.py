# -*- coding: utf-8 -*-

# Copyright (c) 2015 - 2016 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing SSL utility functions.
"""

from __future__ import unicode_literals


def initSSL():
    """
    Function to initialize some global SSL stuff.
    """
    blacklist = [
        "SRP-AES-256-CBC-SHA",          # open to MitM
        "SRP-AES-128-CBC-SHA",          # open to MitM
    ]
    
    try:
        from PyQt5.QtNetwork import QSslSocket
    except ImportError:
        # no SSL available, so there is nothing to initialize
        return
    
    strongCiphers = [c for c in QSslSocket.supportedCiphers()
                     if c.name() not in blacklist and c.usedBits() >= 128]
    QSslSocket.setDefaultCiphers(strongCiphers)
