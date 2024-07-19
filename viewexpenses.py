from globals import user_states, user_timezones, transactions, timezones, categories, bot, DJANGO_TOKEN, server
from timezonehandler import user_has_timezone, get_saved_timezones, get_user_timezone, handle_timezone_selection
from calendarpicker import initiate_calendar_picker, user_date_today
from telebot import types
import requests

def show_view_expenses_date_options(message):
    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    button_options = ['Today', 'Yesterday', 'This week', 'This month', 'Custom date range']
    for option in button_options:
        markup.add(option)
    bot.send_message(chat_id, "For what day:", reply_markup=markup)
    user_states[chat_id] = 'awaiting_view_expenses_date'
    
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_view_expenses_date')
def handle_view_expenses_date(message):
    chat_id = message.chat.id
    max_date = user_date_today(message)
    date_today = max_date.strftime("%Y-%m-%d")
    
    json = {
        'telegram_id':chat_id,
        'timezone': user_timezones[str(chat_id)],
    }

    # Query data from django
    if message.text == 'Today':
        json['date'] = date_today
        r = requests.post(
           f"{server}/ipon_goodbot/get_expenses/",
            headers={"Authorization":f"Bearer {DJANGO_TOKEN}"},
            json=json
        )
        
    elif message.text == 'Custom date range':
        handle_view_expenses_date_range(message)
    else:
        bot.send_message(chat_id, "Invalid option. Please choose 'Today' or 'Custom date'.")

    response = r.json()
    print(response)

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