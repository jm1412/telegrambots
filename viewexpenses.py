from globals import user_states, user_timezones, transactions, timezones, categories, bot, DJANGO_TOKEN, server
from timezonehandler import user_has_timezone, get_saved_timezones, get_user_timezone, handle_timezone_selection
from calendarpicker import initiate_calendar_picker, user_date_today
from telebot import types
from datetime import datetime, timedelta
import requests

view_report_options = ['Today', 'Yesterday', 'Custom date range']

def show_view_expenses_date_options(message):
    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    for option in view_report_options:
        markup.add(option)
    bot.send_message(chat_id, "For what day:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_view_expenses_date'
    
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date')
def handle_view_expenses_date(message):
    chat_id = message.chat.id
    max_date = user_date_today(message)
    date_today = max_date.strftime("%Y-%m-%d")
    
    transactions[chat_id] = {
        'telegram_id': chat_id,
        'timezone': user_timezones[str(chat_id)]
    }

    # Custom date range
    if message.text == 'Custom date range':
        user_states[chat_id] = 'awaiting_custom_date'
        handle_view_expenses_date_range(message)

    # Premade options
    elif message.text in view_report_options:
        if message.text == 'Today':
            transactions[chat_id]['date'] = date_today
        elif message.text == 'Yesterday':
            yesterday = max_date - timedelta(days=1)
            transactions[chat_id]['date'] = yesterday.strftime("%Y-%m-%d")

        get_user_expenses(message)

def get_user_expenses(message):
    """
    Gets user transactions from django.
    Uses global transactions which contains chat_id, and dates
        There are three possible dates, 'date', 'from_date', 'to_date',
        'date' is used for single day reports, 'from_date' and 'to_date' are both used to query a range
        the single day date or the range can be None as the django server checks for None-ness.
    """

    r = requests.post(
        f"{server}/ipon_goodbot/get_expenses/",
        headers={"Authorization":f"Bearer {DJANGO_TOKEN}"},
        json=transactions[message.chat.id]
    )
    response = r.json()
    show_expenses(message, response)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date_range')
def handle_view_expenses_date_range(message):
    """
    Calls when a custom date range is required.
    """
    def handle_first_date(date):
        from_date = date.strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, f"From date selected: {from_date}")
        transactions[chat_id]['from_date'] = from_date
        # Now ask for the 'to' date
        initiate_calendar_picker(message, handle_second_date)

    def handle_second_date(date):
        to_date = date.strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, f"To date selected: {to_date}")
        transactions[chat_id]['to_date'] = to_date

        get_user_expenses(message)

    # Start by asking for the 'from' date
    chat_id = message.chat.id
    initiate_calendar_picker(message, handle_first_date)
    
def get_expense_categories():
    """Gets main categories and adds them in a dictionary with a value of 0."""
    main_categories = list(categories.keys())
    expense_categories = {}

    for item in main_categories:
        expense_categories[item] = 0

    return expense_categories

def find_main_category(item):
    """
    Return which main category something belongs to.
    For example: Rent returns Housing since as per global.categories, Rent is a subcategory of Housing
    """

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