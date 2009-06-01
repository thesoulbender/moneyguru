# Unit Name: moneyguru.gui.bar_graph_test
# Created By: Virgil Dupras
# Created On: 2008-08-21
# $Id$
# Copyright 2009 Hardcoded Software (http://www.hardcoded.net)

from datetime import date, timedelta

from hsutil.currency import CAD

from ..main_test import TestCase, CommonSetup
from ..model.account import INCOME

class Pristine(TestCase, CommonSetup):
    def setUp(self):
        self.create_instances()
        self.setup_monthly_range()
    
    def test_cook_bar_overflow(self):
        # When some data is included in a bar that overflows, we must not forget to ensure cooking
        # until the end of the *overflow*, not the end of the date range.
        self.add_account('Checking')
        self.add_account('Income', account_type=INCOME)
        self.add_entry('01/11/2008', transfer='Checking', increase='42') #sunday
        self.document.select_prev_date_range() # oct 2008
        self.add_entry('31/10/2008', transfer='Checking', increase='42')
        # now, the creation of the txn forced a recook. what we want to make sure is that both 
        # entries will be in the bar
        self.assertEqual(self.bar_graph_data()[0][2], '84.00')
    

class ForeignAccount(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('Visa', account_type=INCOME, currency=CAD)
    
    def test_graph(self):
        self.assertEqual(self.bargraph.currency, CAD)
    

class SomeIncomeInTheFutureWithRangeOnYearToDate(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('Checking')
        tomorrow = date.today() + timedelta(1)
        self.add_entry(tomorrow.strftime('%d/%m/%Y'), transfer='Income', increase='42')
        self.document.select_year_to_date_range()
    
    def test_bar_graphs_during_ytd_dont_show_future_data(self):
        # Unlike all other date ranges, bar charts during YTD don't overflow
        self.document.select_income_statement()
        self.assertEqual(len(self.pgraph.data), 0)
    

class SomeIncomeTodayAndInTheFuture(TestCase):
    def setUp(self):
        self.create_instances()
        self.add_account('Checking')
        self.add_account('Income', account_type=INCOME)
        tomorrow = date.today() + timedelta(1)
        self.add_entry(tomorrow.strftime('%d/%m/%Y'), transfer='Checking', increase='12')
        self.add_entry(date.today().strftime('%d/%m/%Y'), transfer='Checking', increase='30')
        self.document.select_year_range()
    
    def test_bar_split_in_two(self):
        # when some amounts are in the future, but part of the same bar, the amounts are correctly
        # split in the data point
        tomorrow = date.today() + timedelta(1)
        if tomorrow.month != date.today().month:
            return # the test will not work on the last day of each month, skip it
        self.assertEqual(self.bargraph.data[0][2:], (30, 12))
    

class AccountAndEntriesAndBudget(TestCase, CommonSetup):
    def setUp(self):
        # Weeks of Jan: 31-6 7-13 14-20 21-27 28-3
        self.create_instances()
        self.setup_monthly_range()
        self.add_account('Account 1', account_type=INCOME)
        self.mock_today(2008, 1, 17)
        self.set_budget('400')
        self.add_entry('10/01/2008', 'Entry 1', increase='100.00')
        self.add_entry('14/01/2008', 'Entry 2', increase='150.00')
    
    def test_cash_flow_with_budget(self):
        # Must include the budget. 250 of the 400 are spent, there's 150 left to add proportionally
        # in the remaining weeks.
        self.assertEqual(self.bargraph.data[0][2:], (100, 0)) # week 2
        # there are 14 days left, week 3 contains 3 of them. Therefore, the budget amount is
        # (150 / 14) * 3 --> 32.14
        self.assertEqual(self.bargraph.data[1][2:], (150, 32.14)) # week 3
    

class RunningYearWithSomeIncome(TestCase):
    def setUp(self):
        self.mock_today(2008, 11, 1)
        self.create_instances()
        self.add_account('Checking')
        self.add_entry('11/09/2008', transfer='Income', increase='42')
        self.add_entry('24/09/2008', transfer='Income', increase='44')
        self.document.select_running_year_range()
    
    def test_monthly_bars(self):
        # with the running year range, the bars are monthly
        self.document.select_income_statement()
        self.assertEqual(len(self.pgraph.data), 1) # there is only one bar
    
