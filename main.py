#
#
#

import logging
import os
from pathlib import Path
from pprint import pprint
import signal
from types import FrameType
from typing import Any, Coroutine

from bale import (
	Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment,
	InlineKeyboardMarkup, InlineKeyboardButton,
	MenuKeyboardMarkup, MenuKeyboardButton)

import app_utils
from app_utils import ConfigureLogging
from db import IDatabase
from db.sqlite3 import SqliteDb
from panels import (GetAdminReply, GetCommandsReply, GetProductsReply,
	GetUserPanelReply ,GetUnknownReply)


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

# Preparing the database ============================================
DB = SqliteDb(APP_DIR / 'db.db3')


def _DispatchCommand(
		message: Message,
		cmd: str | None,
		) -> Coroutine[Any, Any, Message]:
	commandParts = cmd.split()
	commandParts[0] = commandParts[0].lower()
	if commandParts[0] == app_utils.START_CMD:
		return GetUserPanelReply(message)
	elif commandParts[0] == app_utils.PRODUCTS_CMD:
		return GetProductsReply(message)
	elif commandParts[0] == app_utils.HELP_CMD:
		return GetCommandsReply(message)
	elif commandParts[0] == app_utils.ADMIN_CMD:
		return GetAdminReply(message, ADMIN_IDS)
	else:
		return GetUnknownReply(message)

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
	# Looking for empty or None messages...
	if not message.content:
		logging.warning('an empty or None message')
		return
	await _DispatchCommand(message, message.text)

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
	if not callback.data:
		logging.info('A callback with no data.')
		return
	await _DispatchCommand(callback.message, callback.data)

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


def CloseBot(signal: int, frame: FrameType) -> None:
	import asyncio
	async def _CloseBot() -> None:
		DB.Close()
		await happyEngBot.close()
	print('Closing the Bot...')
	asyncio.create_task(_CloseBot())

signal.signal(signal.SIGINT, CloseBot)

happyEngBot.run()
