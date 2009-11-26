# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2009-11-22
# $Id$
# Copyright 2009 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLineEdit

# The QCompleter works by having access to a list of possible matches, but we already have that
# logic implemented on the model side. It turns out subclassing the QCompleter to adapt it to our
# case would have been more complex than subclassing a QLineEdit.

# Moreover, QCompleter's behavior on up/down arrow is inadequate in InlineCompletion mode (doesn't
# cycle through possible completions)

# For a CompletableEdit to work, its model/attrname attributes *have* to be set. model has to be
# something that has complete(value, attrname), current_completion(), next_completion() and 
# prev_completion().

class CompletableEdit(QLineEdit):
    ATTRNAME = None # must be set
    
    def __init__(self, parent):
        QLineEdit.__init__(self, parent)
        self.model = None
    
    def _prefix(self):
        # Returns the text before the selection, lowered
        if self.selectionStart() == -1:
            return unicode(self.text()).lower()
        else:
            return unicode(self.text()[:self.selectionStart()]).lower()
    
    def _replaceText(self, newText):
        # Replaces self.text() with newText while keeping the selection intact (for up/down cycling)
        if not newText:
            return
        selectionStart = self.selectionStart()
        if selectionStart == -1: # has been lost somehow, so it means the whole text is the prefix
            selectionStart = len(self.text())
        self.setText(newText)
        self.setSelection(selectionStart, len(newText) - selectionStart)
    
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up:
            self._replaceText(self.model.prev_completion())
        elif key == Qt.Key_Down:
            self._replaceText(self.model.next_completion())
        else:
            oldPrefix = self._prefix()
            QLineEdit.keyPressEvent(self, event)
            newPrefix = self._prefix()
            if oldPrefix != newPrefix: # text changed, do completion
                completion = self.model.complete(newPrefix, self.ATTRNAME)
                if completion:
                    self.setText(completion)
                    self.setSelection(len(newPrefix), len(completion) - len(newPrefix))
    

class DescriptionEdit(CompletableEdit):
    ATTRNAME = 'description'

class PayeeEdit(CompletableEdit):
    ATTRNAME = 'payee'

class AccountEdit(CompletableEdit):
    ATTRNAME = 'account'