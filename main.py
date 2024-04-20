#
#
#

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine

from bale import (
    Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment)

from cmds import Page, AbsWizard
from db import IDatabase
from utils.types import InputType, UserInput, UserPool


# Bot-wide variables ================================================
_APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

ADMIN_IDS: tuple[int, ...]
"""A tuple of ID's of admin users."""

_TOKEN: str
"""The token of the Bale bot."""

_happyEngBot: Bot
"""The Bot object for this @happy_eng_bot."""

db: IDatabase
"""The database of the Bot."""

pUsers = UserPool()
"""A mapping of `ID -> UserData` contains all information of recent users
of the Bot.
"""

pages: dict[str, Callable] = {}

wizards: dict[str, AbsWizard] = {}


def _LoadConfig() -> None:
	# Declaring variables ---------------------------------
	import tomllib
	global ADMIN_IDS
	global _TOKEN
	# Functionality ---------------------------------------
	with open(_APP_DIR / 'config.toml', mode='rb') as tomlObj:
		settings = tomllib.load(tomlObj)
		ADMIN_IDS = settings['ADMIN_IDS']
		_TOKEN = settings['BALE_BOT_TOKEN']


def _LoadDatabase() -> None:
	"""Loads database."""
	# Declaring variables ---------------------------------
	from db.sqlite3 import SqliteDb
	global db
	# Loading database ------------------------------------
	db = SqliteDb(_APP_DIR / 'db.db3')


def _LoadPagesWizards() -> None:
	# Declaring variables ---------------------------------
	import cmds
	from importlib import import_module
	from types import ModuleType
	global ADMIN_IDS
	global db
	global pUsers
	global pages
	global wizards
	modsDir: Path
	modNames: list[Path]
	modName: Path
	modObj: ModuleType
	# Loading pages & wizards -----------------------------
	# Initializing root module of commands package...
	botVars = {
		'ADMIN_IDS_': ADMIN_IDS,
		'db_': db,
		'pUsers_': pUsers,
		'pages_': pages,
		'wizards_': wizards,}
	cmds.InitModule(**botVars)
	pages.update({pg.cmd:pg.callback for pg in cmds.GetPages()})
	wizards.update({wiz.CMD:wiz for wiz in cmds.GetWizards()})
	# Initializing & loading the other module of commands package...
	modsDir = _APP_DIR / 'cmds'
	modNames = list(modsDir.glob('*.py'))
	modNames = [modName.relative_to(modsDir) for modName in modNames]
	try:
		modNames.remove(Path('__init__.py'))
	except ValueError:
		pass
	for modName in modNames:
		try:
			modObj = import_module(f'cmds.{modName.stem}')
			modObj.InitModule(**botVars)
			modPages: tuple[Page, ...] = modObj.GetPages()
			modWizards: tuple[AbsWizard, ...] = modObj.GetWizards()
			dPages = {page.cmd:page.callback for page in modPages}
			dWizards = {wiz.CMD:wiz for wiz in modWizards}
		except Exception:
			logging.error(f'E1-2: {modName.absolute()}')
			continue
		# Loading pages...
		for cmd, cb in dPages.items():
			if cmd in pages:
				logging.error(f'E1-10: {cmd}, {pages[cmd].__module__}, '
					f'{modName.__module__}')
			elif cmd in wizards:
				logging.error(f'E1-11: {cmd}, {wizards[cmd].__module__}, '
					f'{modName.__module__}')
			else:
				pages[cmd] = cb
		# Loading wizards...
		for cmd, wiz in dWizards.items():
			if cmd in pages:
				logging.error(f'E1-12: {cmd}, {pages[cmd].__module__}, '
					f'{modName.__module__}')
			elif cmd in wizards:
				logging.error(f'E1-13: {cmd}, {wizards[cmd].__module__}, '
					f'{modName.__module__}')
			else:
				wizards[cmd] = wiz
		pages.update(dPages)
		wizards.update(dWizards)


def _InitOtherModules() -> None:
	# Declaring variables ---------------------------------
	import utils.types
	global ADMIN_IDS
	global db
	global pUsers
	global pages
	global wizards
	# Functioning -----------------------------------------
	botVars = {
		'ADMIN_IDS_': ADMIN_IDS,
		'db_': db,
		'pUsers_': pUsers,
		'pages_':pages,
		'wizards_': wizards,}
	utils.types.InitModule(**botVars)


async def _DispatchInput(
		bale_msg: Message,
		bale_user: User,
		type_: InputType,
		input_: str | None,
		) -> Coroutine[Any, Any, None]:
	"""Disptaches the user input."""
	inputExists = pUsers[bale_user.id].CountInputs() > 0
	pUsers[bale_user.id].ApendInput(UserInput(bale_msg, type_, input_))
	pUsers[bale_user.id]._baleUser = bale_user
	pUsers[bale_user.id]._dbUser.Frequencies.Increment(bale_msg.date.hour)
	if inputExists:
		return
	while pUsers[bale_user.id].CountInputs() > 0:
		pUsers[bale_user.id].ReplyNextInput()


def _CreateBot() -> None:
	# Declaring of variables ------------------------------
	global _happyEngBot
	# Functionality ---------------------------------------
	_happyEngBot = Bot(token=_TOKEN)

	@_happyEngBot.event
	async def on_before_ready() -> None:
		logging.debug("'on_before_ready' event is raised.")

	@_happyEngBot.event
	async def on_ready():
		logging.debug(f"{_happyEngBot.user.username} is ready to respond!")

	@_happyEngBot.event
	async def on_message(bale_msg: Message):
		# Looking for empty or None messages...
		if not bale_msg.content:
			logging.warning('an empty or None message')
			return
		if bale_msg.content.startswith('/'):
			await _DispatchInput(
				bale_msg,
				bale_msg.from_user,
				InputType.COMMAND,
				bale_msg.text,)
		else:
			await _DispatchInput(
				bale_msg,
				bale_msg.from_user,
				InputType.TEXT,
				bale_msg.text,)

	@_happyEngBot.event
	async def on_message_edit(message: Message) -> None:
		logging.debug('A message is edited '.ljust(70, '='))
		logging.debug(message)

	@_happyEngBot.event
	async def on_update(update: Update) -> None:
		logging.debug('An update is received '.ljust(70, '='))
		logging.debug(update)

	@_happyEngBot.event
	async def on_callback(bale_cb: CallbackQuery) -> None:
		logging.debug('A callback query is created '.ljust(70, '='))
		logging.debug(bale_cb)
		# Looking for empty or None messages...
		if not bale_cb.data:
			logging.info('A callback with no data.')
			return
		if bale_cb.data.startswith('/'):
			await _DispatchInput(
				bale_cb.message,
				bale_cb.from_user,
				InputType.COMMAND,
				bale_cb.data,)
		else:
			await _DispatchInput(
				bale_cb.message,
				bale_cb.from_user,
				InputType.CALLBACK,
				bale_cb.data,)

	@_happyEngBot.event
	async def on_member_chat_join(
			message: Message,
			chat: Chat,
			user: User
			) -> None:
		logging.debug('A user has been added to a chat '.ljust(70, '='))
		logging.debug(message)
		logging.debug(chat)
		logging.debug(user)

	@_happyEngBot.event
	async def on_member_chat_leave(
			message: Message,
			chat: Chat,
			user: User
			) -> None:
		logging.debug('A user has left a chat '.ljust(70, '='))
		logging.debug(message)
		logging.debug(chat)
		logging.debug(user)

	@_happyEngBot.event
	async def on_successful_payment(
			payment: SuccessfulPayment,
			) -> None:
		logging.debug('A successful payment '.ljust(70, '='))
		logging.debug(payment)


async def _StartBot() -> None:
	async with _happyEngBot:
		await _happyEngBot.connect()


def BotMain() -> None:
	"""The entry point of the Bot."""
	# Declaring variables ---------------------------------
	import asyncio
	from logger import ConfigureLogging
	global _happyEngBot
	global pUsers
	global db
	# Starting point --------------------------------------
	ConfigureLogging(_APP_DIR / 'log.log')
	_LoadConfig()
	_LoadDatabase()
	_LoadPagesWizards()
	_InitOtherModules()
	_CreateBot()
	# Running the bot...
	try:
		asyncio.run(_StartBot())
	except KeyboardInterrupt:
		asyncio.create_task(_happyEngBot.close())
	except SystemExit:
		asyncio.create_task(_happyEngBot.close())
	finally:
		pUsers.Clear()
		db.Close()


if __name__ == '__main__':
	BotMain()


# See https://docs.python-bale-bot.ir/en/stable/event.html
# to get more information about events!
