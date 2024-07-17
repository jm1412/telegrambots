import requests
import os
DJANGO_TOKEN = os.environ.get('DJANGO_TOKEN')
from globals import user_states, user_timezones, transactions, timezones, categories

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