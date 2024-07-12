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

user_states = {}
user_timezones = {"1":"1"}
transactions = {}

timezones = [
    'Etc/GMT+12', 'Pacific/Midway', 'Pacific/Honolulu', 'America/Anchorage', 'America/Los_Angeles',
    'America/Denver', 'America/Chicago', 'America/New_York', 'America/Caracas', 'America/Halifax',
    'America/Sao_Paulo', 'Atlantic/South_Georgia', 'Atlantic/Azores', 'Europe/London', 'Europe/Amsterdam',
    'Europe/Athens', 'Europe/Moscow', 'Asia/Tehran', 'Asia/Dubai', 'Asia/Karachi',
    'Asia/Kolkata', 'Asia/Dhaka', 'Asia/Jakarta', 'Asia/Shanghai', 'Asia/Tokyo',
    'Australia/Adelaide', 'Australia/Sydney', 'Pacific/Noumea', 'Pacific/Auckland', 'Pacific/Tongatapu'
]

@bot.message_handler(commands=['viewexpenses'])
def view_expenses(message):
    """Gets called when user initiates /viewexpenses"""
    
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

def user_date_today(message):
    """Returns user date today adjusted for timezone."""
    chat_id = message.chat.id
    user_tz = pytz.timezone(user_timezones[str(chat_id)])
    user_date_today = datetime.now(user_tz).date()
    return user_date_today
    
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date')
def handle_view_expenses_date(message):
    """Accepts date, """
    chat_id = message.chat.id
    max_date = user_date_today(message)
    custom_date = max_date.strftime("%Y-%m-%d")
    if message.text == 'Today':
        transactions[chat_id]["date"] = custom_date
        
        bot.send_message(chat_id, "You selected 'Today'. Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
        user_states[chat_id] = 'awaiting_amount'
    
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
        cal_start(message, handle_second_date)

    def handle_second_date(date):
        to_date = date.strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, f"To date selected: {to_date}")
        # Here you can handle both dates as needed

    # Start by asking for the 'from' date
    cal_start(message, handle_first_date)    


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the bot! Type /help to see available commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Here are the available commands:
    /start - Start the bot
    /help - Show this help message
    /addexpense - Add an expense
    """
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['addexpense'])
def initiate_add_expense(message):
    """Gets called when user initiates /addexpense"""
    chat_id = message.chat.id
    transactions[chat_id] = {"telegram_id":chat_id}
    
    if user_has_timezone(message):
        add_expense_show_calendar_picker(message)
    else:
        get_user_timezone(message)
        
def add_expense_show_calendar_picker(message):      
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    itembtn1 = types.KeyboardButton('Today')
    itembtn2 = types.KeyboardButton('Custom date')
    markup.add(itembtn1, itembtn2)
    bot.send_message(chat_id, "For what day:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_date'
    

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_date')
def handle_date_response(message):
    chat_id = message.chat.id
    max_date = user_date_today(message)
    custom_date = max_date.strftime("%Y-%m-%d")
    if message.text == 'Today':
        transactions[chat_id]["date"] = custom_date
        
        bot.send_message(chat_id, "You selected 'Today'. Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
        user_states[chat_id] = 'awaiting_amount'
    
    elif message.text == 'Custom date':
        cal_start(message, lambda date: handle_custom_date_response(message, date))
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

        bot.send_message(chat_id, f"Please enter the expense amount:")
        user_states[chat_id] = 'awaiting_amount'
    
    except ValueError:# Not needed since date picker is limited by date.today, but added just in case
        bot.send_message(chat_id, "Invalid date. Please enter a valid date in YYYY-MM-DD format that is not in the future.")
        handle_date_response(message)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_amount')
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
    post_expense_entry(message)

def post_expense_entry(message):
    """Saves expense entry to server."""
    chat_id = message.chat.id
    
    #TODO: remove dictionary entry on successful posting
    d = transactions[chat_id]
    d["timezone"] = user_timezones[str(chat_id)]

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
            json={"telegram_id":chat_id}
            ) #TODO, turn this into a GET instead of a POST
        response = r.json()

        bot.send_message(chat_id, f"Total expenses for today: {response['expense_amount_today']}")

# Helper functions
def cal_start(message, callback):
    """Starts the calendar picker."""
    chat_id = message.chat.id
    user_states[chat_id] = {
        'state': 'awaiting_custom_date',
        'callback': callback
    }
    calendar, step = DetailedTelegramCalendar(max_date=max_date).build()
    bot.send_message(
        chat_id,
        f"Select {LSTEP[step]}",
        reply_markup=calendar
    )

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal_callback_handler(callback_query):
    """Handles calendar picker button."""
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

# Work on user timezone
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
        
    return response[0]

def get_user_timezone(message):
    """Starts when a user gets asked to select timezone."""
    chat_id = message.chat.id

    timezone_keyboard = types.InlineKeyboardMarkup()
    for tz in timezones:
        timezone_keyboard.add(types.InlineKeyboardButton(tz, callback_data=tz))

    bot.send_message(chat_id, "Please select your timezone:", reply_markup=timezone_keyboard)
    bot.send_message(chat_id, "Before we can continue, we need to setup your timezone, please select your timezone above.")
    user_states[chat_id] = 'awaiting_timezone'

@bot.callback_query_handler(func=lambda call: call.data in timezones) # Waits for responses that = timezones list
def handle_timezone_selection(call):
    """Waits for timezone response then saves it to django."""
    # global user_timezones
    chat_id = call.message.chat.id
    user_timezones[chat_id] = call.data
    bot.edit_message_text(f"Timezone selected: {call.data}", chat_id, call.message.message_id)
    
    d = {'telegram_id':chat_id, 'timezone':call.data}
    print(f"sending to server: {d}")
    r = requests.post(
        "http://143.198.218.34/ipon_goodbot/save_user_timezone/",
        headers={"Authorization":f"Bearer {DJANGO_TOKEN}"},
        json=d
    )
    

bot.infinity_polling()
