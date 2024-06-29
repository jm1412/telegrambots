import os
import telebot
from telebot import types
from datetime import datetime, date
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

max_date = date.today()
user_states = {}

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
    if message.text == 'Today':
        bot.send_message(chat_id, "You selected 'Today'. Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
        user_states[chat_id] = 'awaiting_amount'
    elif message.text == 'Custom date':
        custom_date = cal_start(message)
        # bot.send_message(chat_id, "Please enter the date (YYYY-MM-DD):", reply_markup=types.ReplyKeyboardRemove())
        # user_states[chat_id] = 'awaiting_custom_date'
    else:
        bot.send_message(chat_id, "Invalid option. Please choose 'Today' or 'Custom date'.")

def handle_custom_date_response(message, date_obj):
    chat_id = message.chat.id
    custom_date = date_obj.strftime("%Y-%m-%d") # Convert datetime object to string for bot message confirmation.
    try:
        # Validate date format and check if it's a past or current date
        if date_obj > datetime.now().date():
            raise ValueError("Date cannot be in the future.")
        bot.send_message(chat_id, f"Please enter the expense amount:")
        user_states[chat_id] = 'awaiting_amount'
    except ValueError:# Not needed since date picker is limited by date.today, but added just in case
        bot.send_message(chat_id, "Invalid date. Please enter a valid date in YYYY-MM-DD format that is not in the future.")
        handle_date_response(message)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_amount')
def handle_amount_response(message):
    chat_id = message.chat.id
    try:
        amount = float(message.text)
        bot.send_message(chat_id, f"Expense of {amount} has been recorded.")
        user_states.pop(chat_id, None)  # Clear the state
    except ValueError:
        bot.send_message(chat_id, "Invalid amount. Please enter a valid number.")

from datetime import date
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

# Define max_date as today's date
max_date = date.today()

def cal_start(message):
    """
    Starts the calendar picker.
    """
    calendar, step = DetailedTelegramCalendar(max_date=max_date).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal_callback_handler(callback_query):
    """
    Handles calendar picker button.
    """
    result, key, step = DetailedTelegramCalendar(max_date=max_date).process(callback_query.data)
    chat_id = callback_query.message.chat.id
    
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              chat_id,
                              callback_query.message.message_id,
                              reply_markup=key)
    elif result:
        handle_custom_date_response(callback_query.message, result)
        custom_date = result.strftime("%Y-%m-%d")
        bot.edit_message_text(f"You selected: {custom_date}.",
                              chat_id,
                              callback_query.message.message_id)



bot.infinity_polling()
