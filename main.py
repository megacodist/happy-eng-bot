#
#
#

import logging
import os
from pathlib import Path
import signal
from types import FrameType
from typing import Any, Callable, Coroutine

from bale import (
	Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment)

from app_utils import ConfigureLogging
from db import IDatabase
from db.sqlite3 import SqliteDb
import lang
from panels import (
	GetAdminReply, GetHelpReply, GetProductsReply, GetUnexDataReply,
	GetUserPanelReply ,GetUnexCommandReply)
from utils.types import (
    AbsOperation, Commands, ID, InputType, OpPool, SDelPool, UserData)


# Bot-wide variables & contants =====================================
APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

import tomllib
ADMIN_IDS: tuple[int, ...]
"""A tuple of ID's of admin users."""
_TOKEN: str
"""The token of the Bale bot."""
with open(APP_DIR / 'config.toml', mode='rb') as tomlObj:
	settings = tomllib.load(tomlObj)
	ADMIN_IDS = settings['ADMIN_IDS']
	_TOKEN = settings['BALE_BOT_TOKEN']

DB: IDatabase
"""The database."""

users: dict[ID, UserData] = {}
"""A mapping of `ID -> UserData` contains all information of recent users
of the Bot.
"""

operations = OpPool()
"""The ongoing operations."""


# Configuring the logger ============================================
ConfigureLogging(APP_DIR / 'log.log')

# Preparing the database ============================================
DB = SqliteDb(APP_DIR / 'db.db3')


def _Dispatch(
		message: Message,
		user: User,
		input_: str | None,
		type_: InputType,
		) -> Coroutine[Any, Any, Message]:
	"""Disptaches the user input."""
	if input_.startswith('/'):
		return _DispatchCmd(message, user, input_)
	elif type_ == InputType.TEXT:
		return _DispatchText(message, user, input_)
	elif type_ == InputType.CALLBACK:
		return _DispatchCallback(message, user, input_)
	else:
		logging.error('E1-2', exc_info=True)


def _DispatchCmd(
		message: Message,
		user: User,
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
	elif commandParts[0] == Commands.SHOWCASE.value:
		return GetProductsReply(message)
	elif commandParts[0] == Commands.SIGN_IN.name:
		pass
	elif commandParts[0] == Commands.START.value:
		return GetUserPanelReply(message, DB, ADMIN_IDS)
	else:
		return GetUnexDataReply(message)


def _DispatchText(
		message: Message,
		user: User,
		text: str | None,
		) -> Coroutine[Any, Any, Message]:
	try:
		operations[user.id].ReplyText(text)
	except KeyError:
		return message.reply(lang.UNEX_DATA)


def _DispatchCallback(
		message: Message,
		user: User,
		callback: str | None,
		) -> Coroutine[Any, Any, Message]:
	pass


# Creating & running the Bot ======================================== 
happyEngBot = Bot(token=_TOKEN)
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
	await _Dispatch(
		message,
		message.from_user,
		message.text,
		InputType.TEXT)

@happyEngBot.event
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
	await _Dispatch(
		callback.message,
		callback.from_user,
		callback.data,
		InputType.CALLBACK)

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

try:
	happyEngBot.run()
finally:
	DB.Close()
