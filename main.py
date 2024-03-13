#
#
#

import os
from pathlib import Path
from pprint import pprint

from bale import (
	Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment,
	InlineKeyboardMarkup, InlineKeyboardButton,
	MenuKeyboardMarkup, MenuKeyboardButton)

from app_utils import ConfigureLogging, LoadLangs
from db import IDatabase
from db.sqlite3 import SqliteDb
from panels import GetAdminReply, GetNewcomerReply, RejectUnknownUser


# Bot-wide variables & contants =====================================
APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

ADMIN_IDS: tuple[int, ...] = (
	1553661656,   # Mohsen's ID in bale.ai
	1141453153)  # Hossein's ID in bale.ai
"""A tuple of ID's of admin users."""

ADMIN_PRM = '/admin'
"""The prompt for admin panel."""

DB: IDatabase
"""The database."""

# Configuring the logger ============================================
ConfigureLogging(APP_DIR / 'log.log')

# Loading languages =================================================
LANGS = LoadLangs(APP_DIR)
"""A dictionary of all installed languages."""

# Preparing the database ============================================
DB = SqliteDb(APP_DIR / 'db.db3')

# Creating & running the Bot ======================================== 
happyEngBot = Bot(token=os.environ.get('BALE_HAPPY_ENG_BOT_TOKEN'))
"""The Bot object for this @happy_eng_bot."""

@happyEngBot.event
async def on_before_ready() -> None:
	print("'on_before_ready' event is raised.")

@happyEngBot.event
async def on_ready():
	print(happyEngBot.user.username, "is ready to respond!")

@happyEngBot.event
async def on_message(message: Message):
	print()
	print('A sent message is received '.ljust(70, '='))
	pprint(message)
	# Rejecting unknown user...
	if message.from_user is None:
		await RejectUnknownUser(message)
	# Checking for being newcomer...
	elif message.from_user.id not in DB.GetAllUserIds():
		await GetNewcomerReply(message, LANGS)
	# Checking the prompt to access admin panel...
	elif message.content is ADMIN_PRM:
		await GetAdminReply(message, ADMIN_IDS)
	elif message.content == '/start':
		replyMarkup = InlineKeyboardMarkup()
		replyMarkup.add(InlineKeyboardButton('مشاهده محصولات'), row=1)
		replyMarkup.add(InlineKeyboardButton('من'), row=2)
		replyMarkup.add(InlineKeyboardButton('تو'), row=2)
		await message.reply(
			'درودهای گرم ما بر شما از Happy English!!!',
			components=replyMarkup)
		if message.chat.is_group_chat:
			# work when message sent in a group
			await message.reply("It's is a special Hi for groups!")
	elif message.contact == '/keys':
		keyboard = MenuKeyboardMarkup()
		keyboard.add(MenuKeyboardButton('من'), row=1)
		keyboard.add(MenuKeyboardButton('تو'), row=2)
		await message.reply('gf uhgu huhfgu', components=keyboard)

async def on_message_edit(message: Message) -> None:
	print()
	print('A sent message is edited '.ljust(70, '='))
	pprint(message)

@happyEngBot.event
async def on_update(update: Update) -> None:
	print()
	print('An update is received from “Bale” servers '.ljust(70, '='))
	pprint(update)

@happyEngBot.event
async def on_callback(callback: CallbackQuery) -> None:
	print()
	print('A callback query is created '.ljust(70, '='))
	pprint(callback)

@happyEngBot.event
async def on_member_chat_join(
		message: Message,
		chat: Chat,
		user: User
		) -> None:
	print()
	print('A user has been added to a chat '.ljust(70, '='))
	pprint(message)
	pprint(chat)
	pprint(user)

@happyEngBot.event
async def on_member_chat_leave(
		message: Message,
		chat: Chat,
		user: User
		) -> None:
	print()
	print('A user has left a chat '.ljust(70, '='))
	pprint(message)
	pprint(chat)
	pprint(user)

@happyEngBot.event
async def on_successful_payment(
		payment: SuccessfulPayment,
		) -> None:
	print()
	print('A successful payment '.ljust(70, '='))
	pprint(payment)

# See https://docs.python-bale-bot.ir/en/stable/event.html
# to get more information about events!

happyEngBot.run()
