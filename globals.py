import os
import telebot

# server switcher
prod_server = "http://143.198.218.34"
test_server = "http://localhost:8000"
server = prod_server

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
DJANGO_TOKEN = os.environ.get('DJANGO_TOKEN')

user_states = {} # used to keep track of where the user currently is to filter which functions should listen for them
user_timezones = {}
transactions = {} # used to keep track of what the user is about to upload/download

# Common timezones
timezones = [
    'Etc/GMT+12', 'Pacific/Midway', 'Pacific/Honolulu', 'America/Anchorage', 'America/Los_Angeles',
    'America/Denver', 'America/Chicago', 'America/New_York', 'America/Caracas', 'America/Halifax',
    'America/Sao_Paulo', 'Atlantic/South_Georgia', 'Atlantic/Azores', 'Europe/London', 'Europe/Amsterdam',
    'Europe/Athens', 'Europe/Moscow', 'Asia/Tehran', 'Asia/Dubai', 'Asia/Karachi',
    'Asia/Kolkata', 'Asia/Dhaka', 'Asia/Jakarta', 'Asia/Shanghai', 'Asia/Tokyo',
    'Australia/Adelaide', 'Australia/Sydney', 'Pacific/Noumea', 'Pacific/Auckland', 'Pacific/Tongatapu'
]

# Common categories, when a main category is selected, the sub-category gets presented if avaiable
categories = {
    "Housing": ["Rent", "Mortagage", "Utilities", "Council Tax"],
    "Transportation": ["Public Transport", "Gas"],
    "Food and Groceries": ["Groceries", "Dining Out", "Snacks and Beverages", "Meal Delivery Services"],
    "Health and Fitness": ["Gym Membership", "Sports", "Medical", "Health Insurance"],
    "Personal Care": ["Haircut", "Toiletries", "Cosmetic and Skincare"],
    "Entertainment and Leisure": ["Hobbies and Activities", "Concerts", "Streaming Subscription"],
    "Shopping": [],
    "Savings and Investments": [],
    "Debt Payments": [],
    "Miscellaneous": []
}