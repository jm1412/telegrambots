import os
import pytz
import telebot
import requests
from telebot import types
from datetime import datetime, date
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
DJANGO_TOKEN = os.environ.get('DJANGO_TOKEN')

from globals import *

# COMMANDS
# Commands should be added at the top to ensure that all / commands get called irregardless of status
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    """ Kept for good luck """
    bot.reply_to(message, "Welcome to the bot! Type /help to see available commands.")
    
@bot.message_handler(commands=['settings'])
def show_settings_button(message):
    """
    Shows settings buttons.
    """
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    itembtn1 = types.KeyboardButton('Change Timezone')
    markup.add(itembtn1)
    bot.send_message(chat_id, "Select:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_settings_choice'
        
@bot.message_handler(commands=['help'])
def send_help(message):
    """
    TODO:
    add simple instructions of what the bot commands are for
    """
    help_text = """
    Here are the available commands:
    /start - Start the bot
    /help - Show this help message
    /addexpense - Add an expense
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['addexpense'])
def initiate_add_expense(message):
    """
    Gets called when user initiates /addexpense
    """
    chat_id = message.chat.id
    user_states.pop(chat_id, None)
    transactions[chat_id] = {"telegram_id":chat_id}
    
    if user_has_timezone(message):
        add_expense_show_calendar_picker(message)
    else:
        get_user_timezone(message)

def reset_user_state(message):
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

def show_view_expenses_date_options(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    itembtn1 = types.KeyboardButton('Today')
    itembtn2 = types.KeyboardButton('Yesterday')
    itembtn3 = types.KeyboardButton('This week')
    itembtn4 = types.KeyboardButton('This month')
    itembtn5 = types.KeyboardButton('Custom date range')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    bot.send_message(chat_id, "For what day:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_view_expenses_date'
    
@bot.message_handler(commands=['viewexpenses'])
def initiate_view_expenses(message):
    """Gets called when user initiates /viewexpenses"""
    reset_user_state(message)
    show_view_expenses_date_options(message)
    
def add_expense_show_calendar_picker(message):      
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    itembtn1 = types.KeyboardButton('Today')
    itembtn2 = types.KeyboardButton('Custom date')
    markup.add(itembtn1, itembtn2)
    bot.send_message(chat_id, "For what day:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_add_expense_date'

def ask_user_for_expense_amount(message):
    bot.send_message(message.chat.id, "Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
    user_states[message.chat.id] = 'awaiting_expense_amount'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_add_expense_date')
def wait_for_add_expense_date(message):
    chat_id = message.chat.id
    max_date = user_date_today(message)
    custom_date = max_date.strftime("%Y-%m-%d")
    
    if message.text == 'Today':
        transactions[chat_id]["date"] = custom_date
        ask_user_for_expense_amount(message)
    
    elif message.text == 'Custom date':
        initiate_calendar_picker(message, lambda date: handle_custom_date_response(message, date))
        # bot.send_message(chat_id, "Please enter the date (YYYY-MM-DD):", reply_markup=types.ReplyKeyboardRemove())
    
    else:
        bot.send_message(chat_id, "Invalid option. Please choose 'Today' or 'Custom date'.")
        
#@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_custom_date')
def handle_custom_date_response(message, date_obj):
    chat_id = message.chat.id
    custom_date = date_obj.strftime("%Y-%m-%d") # Convert datetime object to string for bot message confirmation.
    try:
        # Validate date format and check if it's a past or current date
        if date_obj > datetime.now().date():
            raise ValueError("Date cannot be in the future.")
            
        transactions[chat_id]["date"] = custom_date
        ask_user_for_expense_amount(message)
    
    except ValueError:# Not needed since date picker is limited by date.today, but added just in case
        bot.send_message(chat_id, "Invalid date. Please enter a valid date in YYYY-MM-DD format that is not in the future.")
        wait_for_add_expense_date(message)

def user_date_today(message):
    global user_timezones
    """Returns user date today adjusted for timezone."""
    chat_id = message.chat.id
    user_tz = pytz.timezone(user_timezones[str(chat_id)])
    user_date_today = datetime.now(user_tz).date()
    return user_date_today

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal_callback_handler(callback_query):
    """Handles calendar picker button."""
    max_date = user_date_today(callback_query.message)
    result, key, step = DetailedTelegramCalendar(max_date=max_date).process(callback_query.data)
    chat_id = callback_query.message.chat.id
    
    if not result and key:
        bot.edit_message_text(
            f"Select {LSTEP[step]}",
            chat_id,
            callback_query.message.message_id,
            reply_markup=key
        )
    elif result:
        user_state = user_states.get(chat_id, {})
        callback = user_state.get('callback')
        if callback:
            callback(result)
        custom_date = result.strftime("%Y-%m-%d")
        bot.edit_message_text(
            f"You selected: {custom_date}.",
            chat_id,
            callback_query.message.message_id
        )

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_expense_amount')
def handle_amount_response(message):
    """
    Waits for user to provide amount and checks if it's a valid input.
    """
    chat_id = message.chat.id
    try:
        amount = float(message.text)
        user_states.pop(chat_id, None)  # Clear the state
    except ValueError:
        bot.send_message(chat_id, "Invalid amount. Please enter a valid number.")

    transactions[chat_id]["amount"] = amount
    
    send_expense_categories(chat_id)
    user_states[chat_id] = 'awaiting_main_category'

def send_expense_categories(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(category) for category in categories.keys()]
    markup.add(*buttons)
    bot.send_message(chat_id, "Select an expense category:", reply_markup=markup)
    
def ask_user_for_expense_note(message):
    bot.send_message(message.chat.id, f"Add note for the expense:", reply_markup=types.ReplyKeyboardRemove())
    user_states[message.chat.id] = 'awaiting_note_for_expense'
    
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_main_category')
def handle_main_category_response(message):
    chat_id = message.chat.id
    selected_category = message.text
    
    if selected_category in categories:
        if categories[selected_category]:
            # If there are subcategories, send them
            send_subcategories(chat_id, selected_category)
            transactions[chat_id]['main_category'] = selected_category
            user_states[chat_id] = 'awaiting_sub_category'
        else:
            # If no subcategories, proceed to next step (e.g., asking for expense amount)
            ask_user_for_expense_note(message)
            transactions[chat_id]['category'] = selected_category
    else:
        bot.send_message(chat_id, "Invalid category. Please select a valid expense category.")
        send_expense_categories(chat_id)

def send_subcategories(chat_id, main_category):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton(sub) for sub in categories[main_category]]
    buttons.append("< Back")
    markup.add(*buttons)
    bot.send_message(chat_id, f"Select a subcategory for {main_category}:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_sub_category')
def handle_sub_category_response(message):
    chat_id = message.chat.id
    selected_subcategory = message.text
    
    if any(selected_subcategory in sublist for sublist in categories.values()):
        ask_user_for_expense_note(message)
        transactions[chat_id]['category'] = selected_subcategory
        
    elif selected_subcategory == "< Back":
        send_expense_categories(chat_id)
        user_states[chat_id] = 'awaiting_main_category'
    else:
        bot.send_message(chat_id, "Invalid category. Please select a valid expense category.")
        send_subcategories(chat_id, transactions[chat_id]['main_category'])

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_note_for_expense')
def wait_for_expense_note(message):
    chat_id = message.chat.id
    expense_comment = message.text
    transactions[chat_id]["expense_comment"] = expense_comment[:100]
    post_expense_entry(message)

def post_expense_entry(message):
    chat_id = message.chat.id
    
    #TODO: remove dictionary entry on successful posting
    d = transactions[chat_id]
    user_timezone = user_timezones[str(chat_id)]
    d["timezone"] = user_timezone

    r = requests.post(
        "http://143.198.218.34/ipon_goodbot/goodbot_postexpense/",
        headers={"Authorization":f"Bearer {DJANGO_TOKEN}"},
        json=d
    )
    response = r.json() # {"message":"success"}

    if response['message'] == 'success':

        bot.send_message(chat_id, "Expense posted")

        r = requests.post(
            "http://143.198.218.34/ipon_goodbot/get_expense_amount_today/",
            headers={"Authorization":f"Bearer {DJANGO_TOKEN}"},
            json={"telegram_id":chat_id, "timezone":user_timezone}
            ) #TODO, turn this into a GET instead of a POST
        response = r.json()

        bot.send_message(chat_id, f"Total expenses for today: {response['total']}")
        
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_settings_choice')
def handle_settings_response(message):
    user_response = message.text
    chat_id = message.chat.id
    
    if user_response == "Change Timezone":
        get_user_timezone(message)

def user_has_timezone(message):
    global user_timezones
    chat_id = message.chat.id

    # check if user is already in user_timezones before trying to update it to minimize api calls.
    if str(chat_id) in user_timezones:
        return True
    
    user_timezones = dict(get_saved_timezones(message))
    if str(chat_id) in user_timezones:
        return True
    
    return False

def get_saved_timezones(message): # TODO: rewrite this to retry in the event that server is down.
    """Gets saved timezones from server and saves it to user_timezones"""
    r = requests.get(
        "http://143.198.218.34/ipon_goodbot/get_saved_timezones/",
        headers={"Authorization":f"Bearer {DJANGO_TOKEN}"}
    )
    response = r.json()
    if len(response) == 0:
        return {}

    response_to_dict = {}
    for item in response:
        response_to_dict.update(item)
        
    return response_to_dict

def get_user_timezone(message):
    """Starts when a user gets asked to select timezone."""
    chat_id = message.chat.id

    timezone_keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for tz in timezones:
        timezone_keyboard.add(types.KeyboardButton(tz))

    bot.send_message(chat_id, "Please select your timezone:", reply_markup=timezone_keyboard)
    user_states[chat_id] = 'awaiting_timezone'
    
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_timezone')
def handle_timezone_selection(message):
    """Handles timezone selection from the user."""
    chat_id = message.chat.id
    if message.text in timezones:
        user_timezones[chat_id] = message.text
        bot.send_message(chat_id, f"Saving timezone: {message.text}", reply_markup=types.ReplyKeyboardRemove())
        
        d = {'telegram_id': chat_id, 'timezone': message.text}
        r = requests.post(
            "http://143.198.218.34/ipon_goodbot/save_user_timezone/",
            headers={"Authorization": f"Bearer {DJANGO_TOKEN}"},
            json=d
        )
        user_states.pop(chat_id, None)
        response = r.json()
        if response['message'] == "Success":
            bot.send_message(chat_id, f"Timezone saved.")
        
    else:
        bot.send_message(chat_id, "Invalid timezone. Please select a valid timezone:", reply_markup=timezone_keyboard)
        
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date')
def handle_view_expenses_date(message):
    """Accepts date, """
    chat_id = message.chat.id
    max_date = user_date_today(message)
    custom_date = max_date.strftime("%Y-%m-%d")
    if message.text == 'Today':
        transactions[chat_id]["date"] = custom_date
        
        bot.send_message(chat_id, "You selected 'Today'. Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
        user_states[chat_id] = 'awaiting_expense_amount'
    
    elif message.text == 'Custom date range':
        handle_view_expenses_date_range(message)
    else:
        bot.send_message(chat_id, "Invalid option. Please choose 'Today' or 'Custom date'.")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date_range')
def handle_view_expenses_date_range(message):
    def handle_first_date(date):
        from_date = date.strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, f"From date selected: {from_date}")
        # Now ask for the 'to' date
        initiate_calendar_picker(message, handle_second_date)

    def handle_second_date(date):
        to_date = date.strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, f"To date selected: {to_date}")
        # Here you can handle both dates as needed

    # Start by asking for the 'from' date
    initiate_calendar_picker(message, handle_first_date)
    
def initiate_calendar_picker(message, callback):
    """Starts the calendar picker."""
    chat_id = message.chat.id
    user_states[chat_id] = {
        'state': 'awaiting_custom_date',
        'callback': callback
    }
    max_date = user_date_today(message)
    calendar, step = DetailedTelegramCalendar(max_date=max_date).build()
    bot.send_message(
        chat_id,
        f"Select {LSTEP[step]}",
        reply_markup=calendar
    )



bot.infinity_polling()
