import unittest
from unittest.mock import MagicMock, patch
from globals import categories
from viewexpenses import get_expense_categories, find_main_category, prepare_report, show_expenses
# Import functions from your module

def get_expense_categories():
    """ Gets main categories and adds them in a dictionary with a value of 0."""
    main_categories = list(categories.keys())
    expense_categories = {}

    for item in main_categories:
        expense_categories[item] = 0

    return expense_categories

def find_main_category(item):
    """ Return which category something belongs to. """
    if item in categories:
        return item
    for main_category, subcategories in categories.items():
        if item in subcategories:
            return main_category
    return None    

def prepare_report(expenses):
    """
    Prepares report.
    Takes expenses, list of dictionary from JsonResponse
    Prepares totals per main category.
    Returns formatted string of totals per category.
    """

    report = get_expense_categories() # {category:0, category: 0}
    
    # categorise expense category to respective main category and update total
    for expense in expenses:
        if category := find_main_category(expense['category']):
            report[category] = report[category] + expense['amount_spent']

    # prepare report for sending
    formatted_report = ""
    for item in report.keys():
        formatted_report +=f"{item} : {report[item]} \n"
    
    return formatted_report

def show_expenses(message, expenses):
    """ Show expenses to user by category. """
    report = prepare_report(expenses)
    bot.send_message(message.chat.id, report)

class TestExpenses(unittest.TestCase):

    def test_get_expense_categories(self):
        expected = {
            "Housing": 0,
            "Transportation": 0,
            "Food and Groceries": 0,
            "Health and Fitness": 0,
            "Personal Care": 0,
            "Entertainment and Leisure": 0,
            "Shopping": 0,
            "Savings and Investments": 0,
            "Debt Payments": 0,
            "Miscellaneous": 0
        }
        result = get_expense_categories()
        self.assertEqual(result, expected)

    def test_find_main_category(self):
        self.assertEqual(find_main_category("Rent"), "Housing")
        self.assertEqual(find_main_category("Public Transport"), "Transportation")
        self.assertEqual(find_main_category("Groceries"), "Food and Groceries")
        self.assertEqual(find_main_category("NonExistent"), None)

    def test_prepare_report(self):
        expenses = [
            {'category': 'Rent', 'amount_spent': 1000},
            {'category': 'Mortgage', 'amount_spent': 500},
            {'category': 'Public Transport', 'amount_spent': 150},
            {'category': 'Groceries', 'amount_spent': 200},
            {'category': 'Dining Out', 'amount_spent': 100}
        ]
        expected = (
            "Housing : 1500 \n"
            "Transportation : 150 \n"
            "Food and Groceries : 300 \n"
            "Health and Fitness : 0 \n"
            "Personal Care : 0 \n"
            "Entertainment and Leisure : 0 \n"
            "Shopping : 0 \n"
            "Savings and Investments : 0 \n"
            "Debt Payments : 0 \n"
            "Miscellaneous : 0 \n"
        )
        result = prepare_report(expenses)
        self.assertEqual(result, expected)

    @patch('your_module.bot.send_message')
    def test_show_expenses(self, mock_send_message):
        message = MagicMock()
        expenses = [
            {'category': 'Rent', 'amount_spent': 1000},
            {'category': 'Mortgage', 'amount_spent': 500},
            {'category': 'Public Transport', 'amount_spent': 150},
            {'category': 'Groceries', 'amount_spent': 200},
            {'category': 'Dining Out', 'amount_spent': 100}
        ]
        expected_report = (
            "Housing : 1500 \n"
            "Transportation : 150 \n"
            "Food and Groceries : 300 \n"
            "Health and Fitness : 0 \n"
            "Personal Care : 0 \n"
            "Entertainment and Leisure : 0 \n"
            "Shopping : 0 \n"
            "Savings and Investments : 0 \n"
            "Debt Payments : 0 \n"
            "Miscellaneous : 0 \n"
        )

        show_expenses(message, expenses)
        mock_send_message.assert_called_once_with(message.chat.id, expected_report)

if __name__ == '__main__':
    unittest.main()
