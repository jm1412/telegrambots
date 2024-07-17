import requests
import os
from globals import user_states, user_timezones, transactions, timezones, categories, bot, DJANGO_TOKEN

        
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
    
def ask_user_for_expense_note(message):
    bot.send_message(message.chat.id, f"Add note for the expense:", reply_markup=types.ReplyKeyboardRemove())
    user_states[message.chat.id] = 'awaiting_note_for_expense'
    
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
        