# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2009-11-28
# $Id$
# Copyright 2009 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from PyQt4.QtGui import QDialog

from ui.preferences_panel_ui import Ui_PreferencesPanel

class PreferencesPanel(QDialog, Ui_PreferencesPanel):
    def __init__(self, app):
        QDialog.__init__(self, None)
        self.app = app
        self._setupUi()
    
    def _setupUi(self):
        self.setupUi(self)
    
    def load(self):
        appm = self.app.model
        self.firstWeekdayComboBox.setCurrentIndex(appm.first_weekday)
        self.aheadMonthsSpinBox.setValue(appm.ahead_months)
        self.yearStartComboBox.setCurrentIndex(appm.year_start_month)
        self.autoSaveIntervalSpinBox.setValue(appm.autosave_interval)
        self.scopeDialogCheckBox.setChecked(self.app.prefs.showScheduleScopeDialog)
        self.dereconciliationWarningCheckBox.setChecked(appm.dont_unreconcile)
    
    def save(self):
        appm = self.app.model
        appm.first_weekday = self.firstWeekdayComboBox.currentIndex()
        appm.ahead_months = self.aheadMonthsSpinBox.value()
        appm.year_start_month = self.yearStartComboBox.currentIndex()
        appm.autosave_interval = self.autoSaveIntervalSpinBox.value()
        self.app.prefs.showScheduleScopeDialog = self.scopeDialogCheckBox.isChecked()
        appm.dont_unreconcile = self.dereconciliationWarningCheckBox.isChecked()
    
