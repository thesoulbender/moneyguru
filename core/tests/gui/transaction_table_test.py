# Created By: Virgil Dupras
# Created On: 2008-07-11
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from datetime import date

from nose.tools import eq_

from hsutil.currency import USD

from ..base import TestCase, TestSaveLoadMixin, CommonSetup, TestApp, with_app
from ...gui.transaction_table import TransactionTable
from ...model.date import MonthRange, YearRange

class Pristine(TestCase):
    def setUp(self):
        self.create_instances()
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
    
    def test_add_and_cancel(self):
        """Reverting after an add removes the transaction from the list"""
        self.ttable.add()
        self.ttable.cancel_edits()
        eq_(len(self.ttable), 0)
    
    def test_add_change_and_save(self):
        """The add mechanism works as expected"""
        self.ttable.add()
        eq_(len(self.ttable), 1)
        eq_(self.ttable.selected_indexes, [0])    
        row = self.ttable[0]
        row.description = 'foobar'
        row.from_ = 'some account'
        row.amount = '42'
        self.clear_gui_calls()
        self.ttable.save_edits()
        self.mainwindow.select_income_statement()
        self.istatement.selected = self.istatement.income[0]
        self.istatement.show_selected_account()
        eq_(self.ta.etable_count(), 1)
    
    def test_add_twice_then_save(self):
        """Calling add() while in edition calls save_edits()"""
        # Previously, it wasn't called, causing the row to just stay in the buffer, disapearing at
        # the next refresh
        self.ttable.add()
        self.ttable.add()
        self.ttable.save_edits()
        eq_(len(self.ttable), 2)
    
    def test_delete(self):
        """Don't crash when trying to remove a transaction from an empty list"""
        self.ttable.delete()
        self.assertFalse(self.document.is_dirty())
    
    def test_gui_call_on_filter_applied(self):
        """The ttable's view is refreshed on filter_applied"""
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
        self.sfield.query = 'foobar'
        self.check_gui_calls(self.ttable_gui, ['refresh'])
    
    def test_refresh_on_import(self):
        # When entries are imported, ttable is refreshed
        self.document.date_range = YearRange(date(2007, 1, 1))
        self.clear_gui_calls()
        self.document.parse_file_for_import(self.filepath('qif', 'checkbook.qif'))
        self.iwin.import_selected_pane()
        self.assertNotEqual(len(self.ttable), 0)
        self.check_gui_calls(self.ttable_gui, ['refresh'])
    
    def test_show_from_account(self):
        # show_from_account() when the selected txn has no assigned account does nothing
        self.ttable.show_from_account() # no crash
        self.check_gui_calls_partial(self.mainwindow_gui, not_expected=['show_entry_table'])
    

class EditionMode(TestCase):
    def setUp(self):
        self.create_instances()
        self.mainwindow.select_transaction_table()
        self.ttable.add()
        self.clear_gui_calls()
    
    def test_add_and_save(self):
        """Leaving the from/to columns empty don't auto-create an empty named account"""
        self.ttable.save_edits()
        self.mainwindow.select_income_statement()
        eq_(self.istatement.income.children_count, 2)
    
    def test_change_date_range(self):
        # When changing the date range during edition, stop that edition before the date range changes
        self.document.select_prev_date_range()
        assert self.ttable.edited is None
    
    def test_delete(self):
        """Calling delete() while in edition mode removes the edited transaction and put the table
        out of edition mode.
        """
        self.ttable.delete()
        eq_(len(self.ttable), 0)
        self.ttable.save_edits() # Shouldn't raise anything
    
    def test_duplicate_selected(self):
        # When duplicating a transaction, make sure to stop editing so that we don't get an
        # assertion exception later.
        self.ttable.duplicate_selected()
        assert self.ttable.edited is None
    

class UnassignedTransactionWithAmount(TestCase, TestSaveLoadMixin):
    # TestSaveLoadMixin: Make sure that unassigned transactions are loaded
    def setUp(self):
        self.create_instances()
        self.mainwindow.select_transaction_table()
        self.ttable.add()
        self.ttable[0].amount = '42'
        self.ttable.save_edits()
    
    def test_show_from_account(self):
        # show_from_account() when the selected txn has no assigned account does nothing
        self.ttable.show_from_account() # no crash
        self.check_gui_calls_partial(self.mainwindow_gui, not_expected=['show_entry_table'])
    

class OneTransaction(TestCase):
    def setUp(self):
        self.create_instances()
        self.document.select_month_range()
        self.add_account('first')
        self.add_txn('11/07/2008', 'description', 'payee', from_='first', to='second', amount='42',
            checkno='24')
        self.clear_gui_calls()
    
    def assert_row_has_original_attrs(self, row):
        eq_(row.date, '11/07/2008')
        eq_(row.description, 'description')
        eq_(row.payee, 'payee')
        eq_(row.checkno, '24')
        eq_(row.from_, 'first')
        eq_(row.to, 'second')
        eq_(row.amount, '42.00')
        assert not row.reconciled
    
    def test_add_then_delete(self):
        # calling delete() while being in edition mode just cancels the current edit. it does *not*
        # delete the other txn as well.
        self.ttable.add()
        self.ttable.delete()
        eq_(len(self.ttable), 1)
        assert self.ttable.edited is None
    
    def test_attributes(self):
        eq_(len(self.ttable), 1)
        self.assert_row_has_original_attrs(self.ttable[0])
    
    def test_autofill_amount_format_cache(self):
        # The amount field is correctly autofilled and the cache correctly invalidated
        self.ttable.add()
        self.ttable.edited.amount # cache the format
        self.ttable.edited.description = 'description'
        eq_(self.ttable.edited.amount, '42.00')
    
    def test_can_edit(self):
        # All columns can be edited, except unknown ones
        self.mainwindow.select_transaction_table()
        editable_columns = ['date', 'description', 'payee', 'checkno', 'from', 'to', 'amount']
        for colname in editable_columns:
            assert self.ttable.can_edit_cell(colname, 0)
        assert not self.ttable.can_edit_cell('unknown', 0)
        # It's also possible to call cen_edit_cell() on the row instance
        assert self.ttable[0].can_edit_cell('date')
        assert not self.ttable[0].can_edit_cell('unknown')
    
    def test_cancel_edits(self):
        # cancel_edits() reverts the edited row back to it's old values.
        self.ttable.cancel_edits() # does nothing
        row = self.ttable[0]
        row.date = '12/07/2008'
        self.ttable.cancel_edits()
        # The current implementation keeps the same row instance, but the tests shouldn't require it
        row = self.ttable[0]
        eq_(row.date, '11/07/2008')
    
    def test_change_transaction_gui_calls(self):
        # Changing a transaction results in a refresh and a show_selected_row call
        row = self.ttable[0]
        row.date = '12/07/2008'
        self.ttable.save_edits()
        self.check_gui_calls(self.ttable_gui, ['refresh', 'show_selected_row'])
    
    def test_duplicate_transaction(self):
        # calling duplicate_selected() duplicates the selected transactions
        self.ttable.duplicate_selected()
        eq_(len(self.ttable), 2)
        self.assert_row_has_original_attrs(self.ttable[0])
        self.assert_row_has_original_attrs(self.ttable[1])
    
    def test_duplicate_transactions(self):
        # duplication works when more than one transaction is selected
        self.mainwindow.duplicate_item()
        self.ttable.select([0, 1])
        self.mainwindow.duplicate_item()
        eq_(len(self.ttable), 4)
    
    def test_edit_date_out_of_bounds(self):
        # when the date of the edited row is out of the date range, is_date_in_future() or
        # is_date_in_past() return True
        # (range is 07/2008)
        assert not self.ttable[0].is_date_in_past()
        assert not self.ttable[0].is_date_in_future()
        self.ttable[0].date = '01/08/2008'
        assert self.ttable.edited.is_date_in_future()
        assert not self.ttable.edited.is_date_in_past()
        self.ttable[0].date = '30/06/2008'
        assert not self.ttable.edited.is_date_in_future()
        assert self.ttable.edited.is_date_in_past()
    
    def test_delete(self):
        # Deleting a transaction updates the graph and makes the 'second' account go away.
        self.ttable.delete()
        eq_(len(self.ttable), 0)
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        eq_(list(self.balgraph.data), [])
        eq_(self.account_names(), ['first'])
    
    def test_delete_while_filtered(self):
        # Deleting a txn while a filter is applied correctly refreshes the ttable
        self.sfield.query = 'description'
        self.ttable.delete()
        eq_(len(self.ttable), 0)
    
    def test_edition_mode(self):
        # Initially, no row is edited. setting a row's attr sets the edition mode.
        assert self.ttable.edited is None
        row = self.ttable[0]
        row.date = '12/07/2008'
        assert self.ttable.edited is row
        self.ttable.cancel_edits()
        assert self.ttable.edited is None
        row.date = '12/07/2008'
        self.ttable.save_edits()
        assert self.ttable.edited is None
    
    def test_save_edits(self):
        # save_edits() puts the changes in the buffer down to the model.
        self.mainwindow.select_transaction_table()
        self.ttable.save_edits() # does nothing
        row = self.ttable[0]
        row.date = '12/07/2008'
        row.description = 'foo'
        row.payee = 'bar'
        row.checkno = 'baz'
        row.from_ = 'newfrom'
        row.to = 'newto'
        row.amount = '.42'
        self.ttable.save_edits()
        # This way, we can make sure that what we have in ttable is from the model, not the row buffer
        self.ttable.refresh()
        row = self.ttable[0]
        eq_(row.date, '12/07/2008')
        eq_(row.description, 'foo')
        eq_(row.payee, 'bar')
        eq_(row.checkno, 'baz')
        eq_(row.from_, 'newfrom')
        eq_(row.to, 'newto')
        eq_(row.amount, '0.42')
        # 'newfrom' has been created as an income, and 'newto' as an expense. 'second' has been cleaned
        self.mainwindow.select_income_statement()
        eq_(self.istatement.income.children_count, 3)
        eq_(self.istatement.expenses.children_count, 3)
        eq_(self.istatement.income[0].name, 'newfrom')
        eq_(self.istatement.expenses[0].name, 'newto')
        # now we want to verify that cooking has taken place
        self.istatement.selected = self.istatement.expenses[0]
        self.istatement.show_selected_account()
        row = self.etable[0]
        eq_(row.increase, '0.42')
    
    def test_set_date_in_range(self):
        # Setting the date in range doesn't cause useless notifications.
        self.mainwindow.select_transaction_table()
        self.ttable[0].date = '12/07/2008'
        self.clear_gui_calls()
        self.ttable.save_edits()
        not_expected = ['animate_date_range_backward', 'animate_date_range_forward',
            'refresh_date_range_selector']
        self.check_gui_calls_partial(self.mainwindow_gui, not_expected=not_expected)
    
    def test_set_date_out_of_range(self):
        # Setting the date out of range makes the app's date range change accordingly.
        self.mainwindow.select_transaction_table()
        self.ttable[0].date = '1/08/2008'
        self.clear_gui_calls()
        self.ttable.save_edits()
        eq_(self.document.date_range, MonthRange(date(2008, 8, 1)))
        expected = ['animate_date_range_forward', 'refresh_date_range_selector']
        self.check_gui_calls_partial(self.mainwindow_gui, expected)
    
    def test_set_invalid_amount(self):
        # setting an invalid amount reverts to the old amount
        self.ttable[0].amount = 'foo' # no exception
        eq_(self.ttable[0].amount, '42.00')
    
    def test_set_row_attr(self):
        # Setting a row's attr puts the table in edition mode, changes the row's buffer, but doesn't
        # touch the transaction.
        self.mainwindow.select_transaction_table()
        row = self.ttable[0]
        row.date = '12/07/2008'
        row.description = 'foo'
        row.payee = 'bar'
        row.checkno = 'baz'
        row.from_ = 'newfrom'
        row.to = 'newto'
        row.amount = '.42'
        eq_(row.date, '12/07/2008')
        eq_(row.description, 'foo')
        eq_(row.payee, 'bar')
        eq_(row.checkno, 'baz')
        eq_(row.from_, 'newfrom')
        eq_(row.to, 'newto')
        eq_(row.amount, '0.42')
        # the changes didn't go down to Transaction
        table = TransactionTable(self.ttable_gui, self.mainwindow)
        table.connect()
        self.assert_row_has_original_attrs(table[0])
    
    def test_show_from_account(self):
        # show_from_account() takes the first account in the From column and shows it in etable.
        self.ttable.show_from_account()
        self.check_gui_calls_partial(self.mainwindow_gui, ['show_entry_table'])
        eq_(self.document.shown_account.name, 'first')
    
    def test_show_to_account(self):
        # show_two_account() takes the first account in the To column and shows it in etable.
        self.ttable.show_to_account()
        self.check_gui_calls_partial(self.mainwindow_gui, ['show_entry_table'])
        eq_(self.document.shown_account.name, 'second')
    
    def test_undo_redo_while_filtered(self):
        # undo/redo while a filter is applied correctly refreshes the ttable
        self.sfield.query = 'description'
        self.ttable.delete()
        self.document.undo()
        eq_(len(self.ttable), 1)
        self.document.redo()
        eq_(len(self.ttable), 0)
    

class TransactionLinkedToNumberedAccounts(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('account1', account_number='4242')
        self.add_account('account2', account_number='4241')
        # when entering the transactions, accounts are correctly found if their number is found
        self.add_txn(from_='4242 - account1', to='4241', amount='42')
    
    def test_from_to_column(self):
        # When an account is numbered, the from and to column display those numbers with the name.
        eq_(self.ttable[0].from_, '4242 - account1')
        eq_(self.ttable[0].to, '4241 - account2')
    

class OneTwoWayTransactionOtherWay(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.document.show_selected_account()
        self.add_entry('11/07/2008', transfer='second', increase='42')
    
    def test_attributes(self):
        """The from and to attributes depends on the money flow, not the order of the splits"""
        self.mainwindow.select_transaction_table()
        row = self.ttable[0]
        eq_(row.from_, 'second')
        eq_(row.to, 'first')
        eq_(row.amount, '42.00')
    

#--- Three-way transaction
def app_three_way_transaction():
    app = TestApp()
    app.add_account('first')
    app.doc.show_selected_account()
    app.add_entry('11/07/2008', description='foobar', transfer='second', decrease='42')
    app.tpanel.load()
    app.stable.add()
    row = app.stable.selected_row
    row.account = 'third'
    row.debit = '20'
    app.stable.save_edits()
    app.tpanel.save()
    app.mainwindow.select_transaction_table()
    return app

def test_autofill():
    # when the txn a split, don't autofill the from/to fields
    app = app_three_way_transaction()
    app.ttable.add()
    app.ttable.edited.description = 'foobar'
    eq_(app.ttable.edited.from_, '')
    eq_(app.ttable.edited.to, '')

def test_edit_description():
    # save_edits() works for non-two-way splits.
    app = app_three_way_transaction()
    row = app.ttable[0]
    row.description = 'foobar'
    app.ttable.save_edits() # no crash
    eq_(app.ttable[0].description, 'foobar')

def test_edit_from():
    # When edited, the From column is saved.
    app = app_three_way_transaction()
    row = app.ttable[0]
    row.from_ = 'fourth'
    app.ttable.save_edits()
    eq_(app.ttable[0].from_, 'fourth')

def test_set_amount():
    # Setting the amount value on a split transaction is possible.
    app = app_three_way_transaction()
    app.ttable[0].amount = '43'
    app.ttable.save_edits()
    eq_(app.ttable[0].amount, '43.00')

#--- Three-way multi-currency transaction
def app_three_way_multi_currency_transaction():
    app = TestApp()
    USD.set_CAD_value(0.8, date(2008, 1, 1))
    app.add_account('first')
    app.doc.show_selected_account()
    app.add_entry('11/07/2008', transfer='second', decrease='42')
    app.tpanel.load()
    app.stable.select([1])
    row = app.stable.selected_row
    row.debit = '20 cad'
    app.stable.save_edits()
    app.stable.add()
    row = app.stable.selected_row
    row.account = 'third'
    row.debit = '22 usd'
    app.stable.save_edits()
    txn = app.tpanel.original
    app.tpanel.save()
    app.mainwindow.select_transaction_table()
    return app

#--- Generators
def test_attributes():
    def check(app, index, expected):
        row = app.ttable[index]
        for attrname, value in expected.items():
            eq_(getattr(row, attrname), value)
    
    # Transactions with more than 2 splits are supported.
    app = app_three_way_transaction()
    yield check, app, 0, {'from_': 'first', 'to': 'second, third', 'amount': '42.00'}
    
    # When the 'to' side has more than one currency, convert everything to the account's currency.
    app = app_three_way_multi_currency_transaction()
    # (42 + 22 + (20 / .8)) / 2
    yield check, app, 0, {'amount': '44.50'}

def test_can_edit():
    def check(app, index, uneditable_fields):
        for colname in ['date', 'description', 'payee', 'checkno', 'from', 'to', 'amount']:
            if colname in uneditable_fields:
                assert not app.ttable.can_edit_cell(colname, index)
            else:
                assert app.ttable.can_edit_cell(colname, index)                
    
    # All fields are editable except "to" which contains 2 accounts (from has only one so it's
    # editable).
    app = app_three_way_transaction()
    yield check, app, 0, ('to', )
    
    # When the transaction is multi-currency, the amount can't be edited.
    app = app_three_way_multi_currency_transaction()
    yield check, app, 0, ('to', 'amount')

class OneFourWayTransactionWithUnassigned(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.document.show_selected_account()
        self.add_entry('11/07/2008', transfer='second', decrease='42')
        self.tpanel.load()
        self.stable.add()
        row = self.stable.selected_row
        row.debit = '20'
        self.stable.save_edits()
        self.stable.add()
        row = self.stable.selected_row
        row.credit = '20'
        self.stable.save_edits()
        self.tpanel.save()
        self.mainwindow.select_transaction_table()
    
    def test_attributes(self):
        """The from/to fields show the unassigned splits"""
        row = self.ttable[0]
        eq_(row.from_, 'first, Unassigned')
        eq_(row.to, 'second, Unassigned')
    

class TwoWayUnassignedWithAmount(TestCase):
    def setUp(self):
        self.create_instances()
        self.mainwindow.select_transaction_table()
        self.ttable.add()
        self.ttable.selected_row.amount = '42'
        self.ttable.save_edits()
    
    def test_null_unassigned_dont_show_up(self):
        """The from/to columns are empty"""
        # previously, they would show "Unassigned"
        row = self.ttable[0]
        eq_(row.from_, '')
        eq_(row.to, '')
    
        
class EmptyTransaction(TestCase):
    def setUp(self):
        self.create_instances()
        self.mainwindow.select_transaction_table()
        self.ttable.add()
        self.ttable.save_edits()
    
    def test_null_unassigned_dont_show_up(self):
        """As opposed to null amounts assigned to accounts, null amounts assign to nothing are ignored"""
        row = self.ttable[0]
        eq_(row.from_, '')
        eq_(row.to, '')
    

class TwoWayNullAmounts(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.document.show_selected_account()
        self.add_entry('11/07/2008', transfer='second')
        self.mainwindow.select_transaction_table()
    
    def test_dont_blank_zero(self):
        """Null amounts are not blanked"""
        row = self.ttable[0]
        eq_(row.amount, '0.00')
        
    def test_from_to(self):
        """When the amounts are null, put everything in from and the last in to"""
        row = self.ttable[0]
        eq_(row.from_, 'first')
        eq_(row.to, 'second')
    

class ThreeWayNullAmounts(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.document.show_selected_account()
        self.add_entry('11/07/2008', transfer='second')
        self.tpanel.load()
        self.stable.add()
        row = self.stable.selected_row
        row.account = 'third'
        self.stable.save_edits()
        self.tpanel.save()
        self.mainwindow.select_transaction_table()
    
    def test_can_edit_to(self):
        """The To column can be edited when it represents a single split"""
        assert self.ttable.can_edit_cell('to', 0)
    
    def test_edit_to(self):
        """When edited, the To column is saved"""
        row = self.ttable[0]
        row.to = 'fourth'
        self.ttable.save_edits()
        eq_(self.ttable[0].to, 'fourth')
    
    def test_from_to(self):
        """When the amounts are null, put everything in from and the last in to"""
        row = self.ttable[0]
        eq_(row.from_, 'first, second')
        eq_(row.to, 'third')
    

class TwoTransactionsOneOutOfRange(TestCase):
    def setUp(self):
        self.create_instances()
        self.document.select_month_range()
        self.add_account()
        self.document.show_selected_account()
        self.add_entry('11/06/2008', description='first')
        self.add_entry('11/07/2008', description='second') # The month range has now changed to July 2008
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
    
    def test_attributes(self):
        """The table only contains transactons in the current date range"""
        eq_(len(self.ttable), 1)
    
    def test_select_prev_date_range(self):
        # The transaction table refreshes itself on date range change
        self.document.select_prev_date_range()
        row = self.ttable[0]
        eq_(row.description, 'first')
        self.check_gui_calls_partial(self.ttable_gui, ['refresh', 'show_selected_row'])
    
    def test_selection_after_date_range_change(self):
        """The selection in the document is correctly updated when the date range changes"""
        # The tpanel loads the document selection, so this is why we test through it.
        self.document.select_prev_date_range()
        self.tpanel.load()
        eq_(self.tpanel.description, 'first')
    

class ThreeTransactionsInRange(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.document.show_selected_account()
        self.add_entry('11/07/2008', description='first', transfer='first')
        self.add_entry('11/07/2008', description='second', transfer='second')
        self.add_entry('12/07/2008', description='third', transfer='third') 
        self.mainwindow.select_transaction_table()
    
    def test_add_date_and_selection(self):
        """New transactions are added on the same date as the currently selected transaction, after
        all transactions of the same date.
        """
        self.ttable.select([0])
        self.ttable.add()
        row = self.ttable.edited
        eq_(row.date, '11/07/2008')
        eq_(self.ttable.selected_indexes, [2])
    
    def test_delete_last(self):
        """Deleting the last txn makes the selection goes one index before"""
        self.ttable.delete()
        eq_(self.ttable.selected_indexes, [1])
    
    def test_delete_multiple_selection(self):
        """delete() when having multiple entries selected delete all selected entries"""
        self.ttable.select([0, 2])
        self.ttable.delete()
        eq_(self.transaction_descriptions(), ['second'])
    
    def test_delete_entries_second(self):
        """Deleting a txn that is not the last does not change the selected index"""
        self.ttable.select([1])
        self.ttable.delete()
        eq_(self.ttable.selected_indexes, [1])
    
    def test_delete_first(self):
        # Deleting the first entry keeps the selection on the first index
        self.ttable.select([0])
        self.ttable.delete()
        eq_(self.ttable.selected_indexes, [0])
    
    def test_delete_second_then_add(self):
        # When deleting the second entry, the 3rd end up selected. if we add a new txn, the txn date
        # must be the date from the 3rd txn
        self.ttable.select([1])
        self.ttable.delete()
        self.ttable.add()
        eq_(self.ttable.edited.date, '12/07/2008')
    
    def test_explicit_selection(self):
        """Only the explicit selection is sticky. If the non-explicit selection changes, this 
        doesn't affect the ttable selection.
        """
        self.mainwindow.select_income_statement()
        self.istatement.selected = self.istatement.income[1] # second
        self.istatement.show_selected_account()
        self.mainwindow.select_transaction_table()
        eq_(self.ttable.selected_indexes, [2]) # explicit selection
        # the other way around too
        self.ttable.select([1])
        self.mainwindow.select_income_statement()
        self.istatement.selected = self.istatement.income[2]
        self.istatement.show_selected_account()
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        eq_(self.etable.selected_indexes, [1]) # explicit selection
    
    def test_selection(self):
        # TransactionTable stays in sync with EntryTable.
        self.ttable.disconnect() # this disconnect scheme will eventually be embedded in the main testcase
        self.etable.select([0, 1])
        self.clear_gui_calls()
        self.etable.disconnect()
        self.ttable.connect()
        eq_(self.ttable.selected_indexes, [0, 1])
        self.check_gui_calls(self.ttable_gui, ['refresh', 'show_selected_row'])
    
    def test_selection_changed_when_filtering_out(self):
        # selected transactions becoming filtered out are not selected anymore. Also, the selection
        # is updated at the document level
        self.ttable.select([0]) # first
        self.sfield.query = 'second'
        eq_(self.ttable.selected_row.description, 'second')
        self.mainwindow.edit_item()
        eq_(self.tpanel.description, 'second')
    

class ThreeTransactionsEverythingReconciled(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('first')
        self.add_account('second')
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[0]
        self.bsheet.show_selected_account()
        self.add_entry('19/07/2008', description='entry 1', increase='1')
        self.add_entry('20/07/2008', description='entry 2', transfer='second', increase='2')
        self.add_entry('20/07/2008', description='entry 3', increase='3')
        self.document.toggle_reconciliation_mode()
        self.etable[0].toggle_reconciled()
        self.etable[1].toggle_reconciled()
        self.etable[2].toggle_reconciled()
        self.mainwindow.select_balance_sheet()
        self.bsheet.selected = self.bsheet.assets[1]
        self.bsheet.show_selected_account()
        self.etable[0].toggle_reconciled() # we also reconcile the other side of the 2nd entry
        self.document.toggle_reconciliation_mode() # commit reconciliation
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
    
    def test_move_while_filtered(self):
        # The ttable is correctly updated after a move with a filter applied
        self.sfield.query = 'entry'
        self.ttable.move([1], 3)
        eq_(self.ttable[1].description, 'entry 3')
        eq_(self.ttable[2].description, 'entry 2')
    
    def test_row_reconciled(self):
        self.assertTrue(self.ttable[0].reconciled)
    

#--- Transaction created through the ttable
def app_transaction_created_through_ttable():
    app = TestApp()
    app.mw.select_transaction_table()
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'foo'
    row.payee = 'bar'
    row.from_ = 'first'
    row.to = 'second'
    row.amount = '42'
    app.ttable.save_edits()
    return app

@with_app(app_transaction_created_through_ttable)
def test_completion(app):
    # Here, we want to make sure that complete() works, but we also want to make sure it is 
    # unaffected by entries (which means selected account and stuff).
    # There is *no* selected account
    ce = app.completable_edit('description')
    ce.text = 'f'
    eq_(ce.completion, 'oo')
    ce.attrname = 'payee'
    ce.text = 'b'
    eq_(ce.completion, 'ar')
    ce.attrname = 'from'
    ce.text = 'f'
    eq_(ce.completion, 'irst')
    ce.text = 's'
    eq_(ce.completion, 'econd')
    ce.attrname = 'to'
    ce.text = 'f'
    eq_(ce.completion, 'irst')
    ce.text = 's'
    eq_(ce.completion, 'econd')

class TransactionCreatedThroughTheTransactionTable(TestCase):
    def setUp(self):
        self.create_instances()
    

class LoadFile(TestCase):
    def setUp(self):
        self.create_instances()
        self.document.date_range = MonthRange(date(2008, 2, 1))
        self.document.load_from_xml(self.filepath('moneyguru', 'simple.moneyguru'))
        self.mainwindow.select_transaction_table()
    
    def test_add_txn(self):
        # The newly added txn will have the last transactions' date rather then today's date
        self.ttable.add()
        eq_(self.ttable.edited.date, '19/02/2008')
    
    def test_attributes(self):
        """The transaction table refreshes upon FILE_LOADED"""
        eq_(len(self.ttable), 4)
        eq_(self.ttable.selected_indexes, [3])
    

#--- Autofill
def app_autofill():
    app = TestApp()
    app.add_account('Checking')
    app.doc.show_selected_account()
    app.add_entry('10/10/2007', 'Deposit', payee='Payee', transfer='Salary', increase='42')
    return app

@with_app(app_autofill)
def test_autofill_after_column_change(app):
    # When setting the Table's columns, only the columns to the right of the edited are auto-filled.
    app.ttable.change_columns(['from', 'description', 'to', 'amount']) # payee is not there
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'Deposit'
    eq_(row.amount, '42.00')
    eq_(row.payee, '')
    eq_(row.from_, '')
    eq_(row.to, 'Checking')

@with_app(app_autofill)
def test_autofill_doesnt_overwrite_nonblank_fields(app):
    # Autofill doesn't touch fields that have a non-blank value.
    app.ttable.add()
    row = app.ttable.edited
    row.payee = 'foo'
    row.from_ = 'bar'
    row.to = 'baz'
    row.amount = '12'
    row.description = 'Deposit'
    eq_(row.amount, '12.00')
    eq_(row.payee, 'foo')
    eq_(row.from_, 'bar')
    eq_(row.to, 'baz')
    app.ttable.cancel_edits()
    # Now we need another row to try for description
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'foo'
    row.payee = 'Payee'
    eq_(row.description, 'foo')

@with_app(app_autofill)
def test_autofill_is_case_sensitive(app):
    # When the case of a description/transfer value does not match an entry, completion do not occur.
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'deposit'
    row.from_ = 'deposit'
    row.to = 'deposit'
    eq_(row.amount, '0.00')

@with_app(app_autofill)
def test_autofill_ignores_blank(app):
    # Blank values never result in autofill.
    app.mw.select_transaction_table()
    row = app.ttable[0]
    row.description = ''
    app.ttable.save_edits()
    app.ttable.add()
    row = app.ttable.edited
    row.description = ''
    eq_(row.payee, '')

@with_app(app_autofill)
def test_autofill_on_set_from(app):
    # Setting 'from' autocompletes the rest.
    app.ttable.add()
    row = app.ttable.edited
    row.from_ = 'Salary'
    eq_(row.amount, '42.00')
    eq_(row.description, 'Deposit')
    eq_(row.payee, 'Payee')
    eq_(row.to, 'Checking')

@with_app(app_autofill)
def test_autofill_on_set_to(app):
    # Setting 'from' autocompletes the rest.
    app.ttable.add()
    row = app.ttable.edited
    row.to = 'Checking'
    eq_(row.amount, '42.00')
    eq_(row.description, 'Deposit')
    eq_(row.payee, 'Payee')
    eq_(row.from_, 'Salary')

@with_app(app_autofill)
def test_autofill_on_set_description(app):
    # Setting a description autocompletes the amount and the transfer.
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'Deposit'
    eq_(row.amount, '42.00')
    eq_(row.payee, 'Payee')
    eq_(row.from_, 'Salary')
    eq_(row.to, 'Checking')

@with_app(app_autofill)
def test_autofill_on_set_payee(app):
    # Setting a transfer autocompletes the amount and the description.
    app.ttable.add()
    row = app.ttable.edited
    row.payee = 'Payee'
    eq_(row.amount, '42.00')
    eq_(row.description, 'Deposit')
    eq_(row.from_, 'Salary')
    eq_(row.to, 'Checking')

@with_app(app_autofill)
def test_autofill_only_when_the_value_changes(app):
    # When editing an existing entry, don't autofill if the value set hasn't changed
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'Deposit' # everything is autofilled
    row.payee = ''
    row.description = 'Deposit'
    eq_(row.payee, '')

@with_app(app_autofill)
def test_autofill_uses_the_latest_entered(app):
    # Even if the date is earlier, we use this newly added entry because it's the latest modified.
    app.add_entry('9/10/2007', 'Deposit', increase='12.34')
    app.ttable.add()
    row = app.ttable.edited
    row.description = 'Deposit'
    eq_(row.amount, '12.34')

@with_app(app_autofill)
def test_change_columns_fixed_from(app):
    # When 'from_' is passed in change_columns(), it is automatically changed to 'from'
    app.mw.select_transaction_table()
    app.ttable.change_columns(['from_', 'description', 'to', 'amount'])
    app.ttable[0].from_ = 'foo' # no crash


class SevenEntries(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.document.show_selected_account()
        self.document.date_range = MonthRange(date(2008, 1, 1))
        self.add_entry('1/1/2008', description='txn 1')
        self.add_entry('2/1/2008', description='txn 2')
        self.add_entry('2/1/2008', description='txn 3')
        self.add_entry('2/1/2008', description='txn 4')
        self.add_entry('2/1/2008', description='txn 5')
        self.add_entry('3/1/2008', description='txn 6')
        self.add_entry('3/1/2008', description='txn 7')

    def test_can_reorder_entry(self):
        """Move is allowed only when it makes sense"""
        self.mainwindow.select_transaction_table()
        self.assertFalse(self.ttable.can_move([0], 2)) # Not the same date
        self.assertFalse(self.ttable.can_move([2], 0)) # Likewise
        self.assertFalse(self.ttable.can_move([1], 1)) # Moving to the same row doesn't change anything
        self.assertFalse(self.ttable.can_move([1], 2)) # Moving to the next row doesn't change anything
        self.assertTrue(self.ttable.can_move([1], 3))
        self.assertTrue(self.ttable.can_move([1], 4))  # Can move to the end of the day
        self.assertFalse(self.ttable.can_move([3], 4)) # Moving to the next row doesn't change anything
        self.assertTrue(self.ttable.can_move([5], 7))  # Can move beyond the bounds of the entry list
        self.assertFalse(self.ttable.can_move([6], 7)) # Moving to the next row doesn't change anything
        self.assertFalse(self.ttable.can_move([6], 8)) # Out of range destination by 2 doesn't cause a crash
    
    def test_can_reorder_entry_multiple(self):
        """Move is allowed only when it makes sense"""
        self.mainwindow.select_transaction_table()
        self.assertTrue(self.ttable.can_move([1, 2], 4)) # This one is valid
        self.assertFalse(self.ttable.can_move([1, 0], 4)) # from_indexes are on different days
        self.assertFalse(self.ttable.can_move([1, 2], 3)) # Nothing moving (just next to the second index)
        self.assertFalse(self.ttable.can_move([1, 2], 1)) # Nothing moving (in the middle of from_indexes)
        self.assertFalse(self.ttable.can_move([1, 2], 2)) # same as above
        self.assertFalse(self.ttable.can_move([2, 1], 2)) # same as above, but making sure order doesn't matter
        self.assertTrue(self.ttable.can_move([1, 3], 3)) # Puts 2 between 3 and 4
        self.assertTrue(self.ttable.can_move([1, 3], 1)) # Puts 4 between 2 and 3
        self.assertTrue(self.ttable.can_move([1, 3], 2)) # same as above
    
    def test_change_date(self):
        """When chaing a txn date, the txn goes at the last position of its new date"""
        self.mainwindow.select_transaction_table()
        self.ttable.select([2]) # txn 3
        row = self.ttable[2]
        row.date = '3/1/2008'
        self.ttable.save_edits()
        eq_(self.ttable[6].description, 'txn 3')
        eq_(self.ttable.selected_indexes, [6])
    
    def test_move_entry_to_the_end_of_the_day(self):
        """Moving a txn to the end of the day works"""
        self.mainwindow.select_transaction_table()
        self.ttable.move([1], 5)
        eq_(self.transaction_descriptions()[:5], ['txn 1', 'txn 3', 'txn 4', 'txn 5', 'txn 2'])
    
    def test_move_entry_to_the_end_of_the_list(self):
        """Moving a txn to the end of the list works"""
        self.mainwindow.select_transaction_table()
        self.ttable.move([5], 7)
        eq_(self.transaction_descriptions()[5:], ['txn 7', 'txn 6'])
    
    def test_reorder_entry(self):
        """Moving a txn reorders the entries."""
        self.mainwindow.select_transaction_table()
        self.ttable.move([1], 3)
        eq_(self.transaction_descriptions()[:4], ['txn 1', 'txn 3', 'txn 2', 'txn 4'])
    
    def test_reorder_entry_multiple(self):
        """Multiple txns can be re-ordered at once"""
        self.mainwindow.select_transaction_table()
        self.ttable.move([1, 2], 4)
        eq_(self.transaction_descriptions()[:4], ['txn 1', 'txn 4', 'txn 2', 'txn 3'])
    
    def test_reorder_entry_makes_the_app_dirty(self):
        """reordering txns makes the app dirty"""
        self.save_file()
        self.mainwindow.select_transaction_table()
        self.ttable.move([1], 3)
        self.assertTrue(self.document.is_dirty())
    
    def test_selection_follows(self):
        """The selection follows when we move the selected txn."""
        self.mainwindow.select_transaction_table()
        self.ttable.select([1])
        self.ttable.move([1], 3)
        eq_(self.ttable.selected_indexes, [2])
        self.ttable.move([2], 1)
        eq_(self.ttable.selected_indexes, [1])
    
    def test_selection_follows_multiple(self):
        """The selection follows when we move the selected txns"""
        self.mainwindow.select_transaction_table()
        self.ttable.select([1, 2])
        self.ttable.move([1, 2], 4)
        eq_(self.ttable.selected_indexes, [2, 3])
    
    def test_selection_stays(self):
        """The selection stays on the same txn if we don't move the selected one"""
        self.mainwindow.select_transaction_table()
        self.ttable.select([2])
        self.ttable.move([1], 3)
        eq_(self.ttable.selected_indexes, [1])
        self.ttable.move([2], 1)
        eq_(self.ttable.selected_indexes, [2])
        self.ttable.select([4])
        self.ttable.move([1], 3)
        eq_(self.ttable.selected_indexes, [4])
    

class FourEntriesOnTheSameDate(TestCase):
    """Four entries in the same account on the same date"""
    def setUp(self):
        self.create_instances()
        self.add_account()
        self.document.show_selected_account()
        self.document.date_range = MonthRange(date(2008, 1, 1))
        self.add_entry('1/1/2008', description='txn 1')
        self.add_entry('1/1/2008', description='txn 2')
        self.add_entry('1/1/2008', description='txn 3')
        self.add_entry('1/1/2008', description='txn 4')
        self.mainwindow.select_transaction_table()
    
    def test_can_reorder_multiple(self):
        """It's not possible to move entries in the middle of a gapless multiple selection"""
        self.assertFalse(self.ttable.can_move([0, 1, 2, 3], 2)) # Nothing moving (in the middle of from_indexes)
    
    def test_move_entries_up(self):
        """Moving more than one entry up does nothing"""
        self.ttable.select([1, 2])
        self.ttable.move_up()
        eq_(self.transaction_descriptions(), ['txn 1', 'txn 2', 'txn 3', 'txn 4'])

    def test_move_entry_down(self):
        """Move an entry down a couple of times"""
        self.ttable.select([2])
        self.ttable.move_down()
        eq_(self.transaction_descriptions(), ['txn 1', 'txn 2', 'txn 4', 'txn 3'])
        self.ttable.move_down()
        eq_(self.transaction_descriptions(), ['txn 1', 'txn 2', 'txn 4', 'txn 3'])

    def test_move_entry_up(self):
        """Move an entry up a couple of times"""
        self.ttable.select([1])
        self.ttable.move_up()
        eq_(self.transaction_descriptions(), ['txn 2', 'txn 1', 'txn 3', 'txn 4'])
        self.ttable.move_up()
        eq_(self.transaction_descriptions(), ['txn 2', 'txn 1', 'txn 3', 'txn 4'])
    

class WithBudget(TestCase, CommonSetup):
    def setUp(self):
        self.create_instances()
        self.setup_account_with_budget()
        self.mainwindow.select_transaction_table()
        self.clear_gui_calls()
    
    def test_budget_spawns(self):
        # When a budget is set budget transaction spawns show up in ttable, at the end of each month.
        eq_(len(self.ttable), 12)
        eq_(self.ttable[0].amount, '100.00')
        eq_(self.ttable[0].date, '31/01/2008')
        eq_(self.ttable[0].to, 'Some Expense')
        assert self.ttable[0].is_budget
        eq_(self.ttable[11].date, '31/12/2008')
        # Budget spawns can't be edited
        assert not self.ttable.can_edit_cell('date', 0)
        self.mainwindow.edit_item() # budget spawns can't be edited
        self.check_gui_calls_partial(self.tpanel_gui, not_expected=['post_load'])
    