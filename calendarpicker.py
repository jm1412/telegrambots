from globals import user_states, bot, user_timezones, transactions
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import pytz
from telebot import types

from datetime import datetime, date

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

def user_date_today(message):
    """Returns user date today adjusted for timezone."""
    chat_id = message.chat.id
    user_tz = pytz.timezone(user_timezones[str(chat_id)])
    user_date_today = datetime.now(user_tz).date()
    return user_date_today
    
#@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_custom_date')
def handle_custom_date_response(message, date_obj, user_state):
    chat_id = message.chat.id
    custom_date = date_obj.strftime("%Y-%m-%d") # Convert datetime object to string for bot message confirmation.
    try:
        # Validate date format and check if it's a past or current date
        if date_obj > datetime.now().date():
            raise ValueError("Date cannot be in the future.")
            
        transactions[chat_id]["date"] = custom_date
        bot.send_message(message.chat.id, "Please enter the expense amount:", reply_markup=types.ReplyKeyboardRemove())
        user_states[message.chat.id] = user_state
    
    except ValueError:# Not needed since date picker is limited by date.today, but added just in case
        bot.send_message(chat_id, "Invalid date. Please enter a valid date in YYYY-MM-DD format that is not in the future.")
        wait_for_add_expense_date(message)



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
        

    
