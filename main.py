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
	Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment)

from app_utils import ConfigureLogging
from db import IDatabase
from db.sqlite3 import SqliteDb
from panels import (GetAdminReply, GetHelpReply, GetProductsReply,
	GetUserPanelReply ,GetUnknownReply)
from utils.types import Commands


# Bot-wide variables & contants =====================================
APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

ADMIN_IDS: tuple[int, ...] = (
	1553661656,   # Mohsen's ID in bale.ai
	1141453153)  # Hossein's ID in bale.ai
"""A tuple of ID's of admin users."""

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
	if commandParts[0] == Commands.ADMIN.value:
		return GetAdminReply(message, ADMIN_IDS)
	elif commandParts[0] == Commands.HELP.value:
		return GetHelpReply(message)
	elif commandParts[0] == Commands.MY_COURSES.name:
		pass
	elif commandParts[0] == Commands.PRODUCTS.value:
		return GetProductsReply(message)
	elif commandParts[0] == Commands.SIGN_IN.name:
		pass
	elif commandParts[0] == Commands.START.value:
		return GetUserPanelReply(message, DB, ADMIN_IDS)
	else:
		return GetUnknownReply(message)

# Creating & running the Bot ======================================== 
happyEngBot = Bot(token=os.environ.get('BALE_HAPPY_ENG_BOT_TOKEN'))
"""The Bot object for this @happy_eng_bot."""

@happyEngBot.event
async def on_before_ready() -> None:
	logging.debug("'on_before_ready' event is raised.")

@happyEngBot.event
async def on_ready():
	logging.debug(f"{happyEngBot.user.username} is ready to respond!")

@happyEngBot.event
async def on_message(message: Message):
	logging.debug('A message is received '.ljust(70, '='))
	logging.debug(message)
	# Looking for empty or None messages...
	if not message.content:
		logging.warning('an empty or None message')
		return
	await _DispatchCommand(message, message.text)

async def on_message_edit(message: Message) -> None:
	logging.debug('A message is edited '.ljust(70, '='))
	logging.debug(message)

@happyEngBot.event
async def on_update(update: Update) -> None:
	logging.debug('An update is received from “Bale” servers '.ljust(70, '='))
	logging.debug(update)

@happyEngBot.event
async def on_callback(callback: CallbackQuery) -> None:
	logging.debug('A callback query is created '.ljust(70, '='))
	logging.debug(f'User: {callback.from_user}')
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
	logging.debug('A user has been added to a chat '.ljust(70, '='))
	logging.debug(message)
	logging.debug(chat)
	logging.debug(user)

@happyEngBot.event
async def on_member_chat_leave(
		message: Message,
		chat: Chat,
		user: User
		) -> None:
	logging.debug('A user has left a chat '.ljust(70, '='))
	logging.debug(message)
	logging.debug(chat)
	logging.debug(user)

@happyEngBot.event
async def on_successful_payment(
		payment: SuccessfulPayment,
		) -> None:
	logging.debug('A successful payment '.ljust(70, '='))
	logging.debug(payment)

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
