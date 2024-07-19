import requests
import os
DJANGO_TOKEN = os.environ.get('DJANGO_TOKEN')

import telebot
from telebot import types

from globals import user_states, user_timezones, transactions, timezones, categories, bot

def user_has_timezone(message):
    chat_id = message.chat.id

    # check if user is already in user_timezones before trying to update it to minimize api calls.
    if str(chat_id) in user_timezones:
        return True
    
    user_timezones.update(dict(get_saved_timezones(message)))
    #user_timezones.update(dict(get_saved_timezones(message)))
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