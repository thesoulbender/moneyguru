# Unit Name: moneyguru.gui.filter_bar_test
# Created By: Virgil Dupras
# Created On: 2008-08-02
# $Id$
# Copyright 2009 Hardcoded Software (http://www.hardcoded.net)

from ..document import (FILTER_UNASSIGNED, FILTER_INCOME, FILTER_EXPENSE, FILTER_TRANSFER,
    FILTER_RECONCILED, FILTER_NOTRECONCILED)
from ..main_test import TestCase
from ..model.account import LIABILITY
from ..reconciliation_test import _ThreeEntriesOneReconciled

class Pristine(TestCase):
    def setUp(self):
        self.create_instances()
    
    def test_attributes(self):
        """the filter bars start out as unfiltered, and both etable and ttable have one"""
        self.assertTrue(self.tfbar.filter_type is None)
        self.assertTrue(self.efbar.filter_type is None)
    

class TransactionsOfEachType(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('asset 1')
        self.add_account('asset 2')
        self.add_entry(description='first', transfer='Income', increase='1')
        self.add_entry(description='second', increase='2')
        self.add_entry(description='third', transfer='Expense', decrease='3')
        self.add_entry(description='fourth', transfer='asset 1', decrease='4')
        self.clear_gui_calls()
    
    def test_efbar_filter_expenses(self):
        #The etable's expense filter makes it only show entries with a decrease
        self.efbar.filter_type = FILTER_EXPENSE # decrease
        self.check_gui_calls(self.etable_gui, refresh=1)
        self.assertEqual(len(self.etable), 2)
        self.assertEqual(self.etable[0].description, 'third')
        self.assertEqual(self.etable[1].description, 'fourth')
        #The ttable's expense filter makes it only show entries with a transfer to an expense.
        self.document.select_transaction_table()
        self.check_gui_calls(self.tfbar_gui, refresh=1) # refreshes on connect()
        self.assertTrue(self.tfbar.filter_type is FILTER_EXPENSE)
        self.assertEqual(len(self.ttable), 1)
        self.assertEqual(self.ttable[0].description, 'third')
    
    def test_efbar_filter_income(self):
        #The etable's income filter makes it only show entries with an increase.
        self.efbar.filter_type = FILTER_INCOME
        self.check_gui_calls(self.etable_gui, refresh=1)
        self.assertEqual(len(self.etable), 2)
        self.assertEqual(self.etable[0].description, 'first')
        self.assertEqual(self.etable[1].description, 'second')
        #The etable's income filter makes it only show entries with a transfer to an income.
        self.document.select_transaction_table()
        self.check_gui_calls(self.tfbar_gui, refresh=1) # refreshes on connect()
        self.assertTrue(self.tfbar.filter_type is FILTER_INCOME)
        self.assertEqual(len(self.ttable), 1)
        self.assertEqual(self.ttable[0].description, 'first')
    
    def test_efbar_filter_transfer(self):
        #The etable's transfer filter makes it only show entries with a transfer to an asset/liability.
        self.efbar.filter_type = FILTER_TRANSFER
        self.check_gui_calls(self.etable_gui, refresh=1)
        self.assertEqual(len(self.etable), 1)
        self.assertEqual(self.etable[0].description, 'fourth')
        self.document.select_transaction_table()
        self.check_gui_calls(self.tfbar_gui, refresh=1) # refreshes on connect()
        self.assertTrue(self.tfbar.filter_type is FILTER_TRANSFER)
        self.assertEqual(len(self.ttable), 1)
        self.assertEqual(self.ttable[0].description, 'fourth')
    
    def test_efbar_filter_unassigned(self):
        """The etable's unassigned filter makes it only show unassigned entries. going to ttable keeps
        the filter on.
        """
        self.efbar.filter_type = FILTER_UNASSIGNED
        self.check_gui_calls(self.etable_gui, refresh=1)
        self.assertEqual(len(self.etable), 1)
        self.assertEqual(self.etable[0].description, 'second')
        self.document.select_transaction_table()
        self.check_gui_calls(self.tfbar_gui, refresh=1) # refreshes on connect()
        self.assertTrue(self.tfbar.filter_type is FILTER_UNASSIGNED)
        self.assertEqual(len(self.ttable), 1)
    
    def test_enable_disable_buttons(self):
        # The enable disable mechanism of the income, expense and transfer buttons work as expected
        self.efbar.filter_type = FILTER_INCOME
        self.document.select_income_statement()
        self.istatement.selected = self.istatement.income[0]
        self.clear_gui_calls()
        self.istatement.show_selected_account()
        self.assertTrue(self.efbar.filter_type is None)
        self.check_gui_calls(self.efbar_gui, refresh=1, disable_transfers=1)
        self.document.select_transaction_table()
        self.check_gui_calls(self.tfbar_gui, refresh=1) # no disable
        self.document.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        self.check_gui_calls(self.efbar_gui, refresh=1, enable_transfers=1)
    
    def test_multiple_filters_at_the_same_time(self):
        """Having an unassigned filter at the same time as a search filter works as expected"""
        self.document.select_transaction_table()
        self.tfbar.filter_type = FILTER_UNASSIGNED
        self.sfield.query = 'first'
        self.assertEqual(len(self.ttable), 0)
    

class ThreeEntriesOneReconciled(_ThreeEntriesOneReconciled):
    def setUp(self):
        _ThreeEntriesOneReconciled.setUp(self)
        self.document.toggle_reconciliation_mode() # commit reonciliation
    
    def test_efbar_not_reconciled(self):
        self.efbar.filter_type = FILTER_NOTRECONCILED
        self.assertEqual(len(self.etable), 2)
        self.assertEqual(self.etable[0].description, 'one')
        self.document.select_transaction_table()
        self.assertEqual(len(self.ttable), 2)
        self.assertEqual(self.ttable[1].description, 'three')
    
    def test_efbar_reconciled(self):
        self.efbar.filter_type = FILTER_RECONCILED
        self.assertEqual(len(self.etable), 1)
        self.assertEqual(self.etable[0].description, 'two')
        self.document.select_transaction_table()
        self.assertEqual(len(self.ttable), 1)
        self.assertEqual(self.ttable[0].description, 'two')
    

class SplitExpenseFromAssetAndLiability(TestCase):
    # A transaction going to an expense, half coming from an asset, the other half coming from a
    # liability
    def setUp(self):
        self.create_instances()
        self.add_account('liability', account_type=LIABILITY)
        self.add_account('asset')
        self.add_entry(transfer='expense', decrease='100')
        self.tpanel.load()
        self.stable.select([0]) # the liability split
        self.stable[0].credit = '50' # lower it to 50, creating an unassigned 50.
        self.stable.save_edits()
        self.stable.select([2])
        self.stable[2].account = 'liability'
        self.stable.save_edits()
        self.tpanel.save()
        self.clear_gui_calls()
        # we're now on etable, looking at 'asset'
    
    def test_efbar_increase_decrease(self):
        self.efbar.filter_type = FILTER_INCOME # increase
        self.assertEqual(len(self.etable), 0)
        self.efbar.filter_type = FILTER_EXPENSE # decrease
        self.assertEqual(len(self.etable), 1)
        # now, let's go to the liability side
        self.document.select_balance_sheet()
        self.bsheet.selected = self.bsheet.liabilities[0]
        self.bsheet.show_selected_account()
        # we're still on FILTER_EXPENSE (decrease)
        self.assertEqual(len(self.etable), 0)
        self.efbar.filter_type = FILTER_INCOME # increase
        self.assertEqual(len(self.etable), 1)
    

if __name__ == '__main__':
    unittest.main()