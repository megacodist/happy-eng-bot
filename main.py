#
#
#

from __future__ import annotations
import gettext
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from bale import (
    Bot, Update, Message, CallbackQuery, Chat, User, SuccessfulPayment)

from db import UserData
from utils.types import (
	AbsInput, AbsPage, AbsWizard, CbInput, CmdInput, TextInput,
	BotVars, UserSpace)


# Bot-wide variables ================================================
_APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

_TOKEN: str
"""The token of the Bale bot."""

_happyEngBot: Bot
"""The Bot object for this @happy_eng_bot."""

botVars = BotVars()
"""This data structure consolidate bot-wide variables."""

_: Callable[[str], str]
"""The `gettext` translator function."""


def _LoadConfig() -> None:
	# Declaring variables ---------------------------------
	import tomllib
	global botVars
	global _TOKEN
	# Functionality ---------------------------------------
	with open(_APP_DIR / 'config.toml', mode='rb') as tomlObj:
		settings = tomllib.load(tomlObj)
		botVars.ADMIN_IDS = settings['ADMIN_IDS']
		_TOKEN = settings['BALE_BOT_TOKEN']


def _LoadDatabase() -> None:
	"""Loads database."""
	# Declaring variables ---------------------------------
	from db.sqlite3 import SqliteDb
	global botVars
	# Loading database ------------------------------------
	botVars.db = SqliteDb(_APP_DIR / 'db.db3')


def _LoadPagesWizards() -> None:
	# Declaring variables ---------------------------------
	import cmds
	from importlib import import_module
	from types import ModuleType
	modsDir: Path
	modNames: list[Path]
	modName: Path
	modObj: ModuleType
	# Loading pages & wizards -----------------------------
	# Initializing root module of commands package...
	botVars.pages.update({pg.CMD:pg for pg in cmds.GetPages()})
	botVars.wizards.update({wiz.CMD:wiz for wiz in cmds.GetWizards()})
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
			modPages: tuple[type[AbsPage], ...] = modObj.GetPages()
			modWizards: tuple[type[AbsWizard], ...] = modObj.GetWizards()
			dPages = {page.CMD:page for page in modPages}
			dWizards = {wiz.CMD:wiz for wiz in modWizards}
		except Exception:
			logging.error(f'E1-2: {(modsDir /modName)}')
			continue
		# Loading pages...
		for cmd, cb in dPages.items():
			if cmd in botVars.pages:
				logging.error(f'E1-10: {cmd}, {botVars.pages[cmd].__module__}, '
					f'{modName.__module__}')
			elif cmd in botVars.wizards:
				logging.error(f'E1-11: {cmd}, {botVars.wizards[cmd].__module__}, '
					f'{modName.__module__}')
			else:
				botVars.pages[cmd] = cb
		# Loading wizards...
		for cmd, wiz in dWizards.items():
			if cmd in botVars.pages:
				logging.error(f'E1-12: {cmd}, {botVars.pages[cmd].__module__}, '
					f'{modName.__module__}')
			elif cmd in botVars.wizards:
				logging.error(f'E1-13: {cmd}, {botVars.wizards[cmd].__module__}, '
					f'{modName.__module__}')
			else:
				botVars.wizards[cmd] = wiz


def _DoOtherInit() -> None:
	# Declaring variables ---------------------------------
	global botVars
	global _
	# Initializing the remaining --------------------------
	botVars.localDir = 'locales'
	botLang = gettext.translation(
		domain='main',
		localedir=botVars.localDir,
		languages=['en',],)
	_ = botLang.gettext


async def _DispatchInput(
		input_: AbsInput,
		bale_user: User,
		) -> None:
	# Declaring variables ---------------------------------
	from cmds import LangSelectPage
	global botVars
	userSpace: UserSpace
	hour: int
	duration: int
	# Diaptching ------------------------------------------
	try:
		userSpace = botVars.pUsers.GetItemBypass(bale_user.id)
	except KeyError:
		if isinstance(input_, CbInput):
			# Creating the new user based on the language...
			userData = UserData(bale_user.id, input_.cb)
			userSpace = UserSpace(userData)
			botVars.pUsers.SetItemBypass(bale_user.id, userSpace)
			# Showing available commands to the newcomer...
			await userSpace.ApendInput(
				CmdInput(input_.bale_msg, bale_user.id, '/help'))
		else:
			await LangSelectPage(input_.bale_msg)
	else:
		userSpace.baleUser = bale_user
		userSpace.dbUser.Frequencies.Increment(input_.bale_msg.date.hour)
		# Getting the suitable life span for the UserSpace object...
		hour = input_.bale_msg.date.hour
		hour = 0 if hour == 23 else (hour + 1)
		duration = userSpace.SuggestLS(hour, botVars.PERCENT_LIFE) + 1
		logging.debug(f"user with {bale_user.id} ID will be in memory for at "
			f"least {duration} hour(s).")
		botVars.pUsers.ScheduleDel(bale_user.id, duration * botVars.MIN_USER_LS)
		# Digesting the user input...
		await userSpace.ApendInput(input_)


def _CreateBot() -> None:
	# Declaring of variables ------------------------------
	global botVars
	global _happyEngBot
	# Functionality ---------------------------------------
	_happyEngBot = Bot(token=_TOKEN)
	botVars.bot = _happyEngBot

	@_happyEngBot.event
	async def on_before_ready() -> None:
		logging.debug("'on_before_ready' event is raised.")

	@_happyEngBot.event
	async def on_ready():
		if _happyEngBot.user is None:
			logging.error(_('FAILED_LOGGED_IN'))
		else:
			logging.debug(_('BOT_READY').format(_happyEngBot.user.username))

	@_happyEngBot.event
	async def on_message(bale_msg: Message):
		# Looking for empty or None messages...
		if not bale_msg.content:
			logging.warning(_('EMPTY_MESSAGE'))
			return
		if bale_msg.from_user is None:
			await bale_msg.reply(_('UNKNOWN_USER'))
			return
		if bale_msg.content.startswith('/'):
			await _DispatchInput(
				CmdInput(bale_msg, bale_msg.from_user.id, bale_msg.content),
				bale_msg.from_user)
		else:
			await _DispatchInput(
				TextInput(bale_msg, bale_msg.from_user.id, bale_msg.content),
				bale_msg.from_user,)

	@_happyEngBot.event
	async def on_message_edit(message: Message) -> None:
		logging.debug(_('MESSAGE_EDITED').ljust(70, '='))
		logging.debug(message)

	@_happyEngBot.event
	async def on_update(update: Update) -> None:
		logging.debug(_('UPDATTE_RECEIVED').ljust(70, '='))
		logging.debug(update)

	@_happyEngBot.event
	async def on_callback(bale_cb: CallbackQuery) -> None:
		logging.debug('A callback query is created '.ljust(70, '='))
		logging.debug(bale_cb)
		# Looking for empty or None messages...
		if bale_cb.message is None:
			return
		if not bale_cb.data:
			logging.info(_('NO_DATA_CB'))
			return
		if bale_cb.data.startswith('/'):
			await _DispatchInput(
				CmdInput(bale_cb.message, bale_cb.from_user.id, bale_cb.data),
				bale_cb.from_user,)
		else:
			await _DispatchInput(
				CbInput(bale_cb.message, bale_cb.from_user.id, bale_cb.data),
				bale_cb.from_user,)

	@_happyEngBot.event
	async def on_member_chat_join(
			message: Message,
			chat: Chat,
			user: User
			) -> None:
		logging.debug(_('USER_JOINED_CHAT').ljust(70, '='))
		logging.debug(message)
		logging.debug(chat)
		logging.debug(user)

	@_happyEngBot.event
	async def on_member_chat_leave(
			message: Message,
			chat: Chat,
			user: User
			) -> None:
		logging.debug(_('USER_LEFT_CHAT').ljust(70, '='))
		logging.debug(message)
		logging.debug(chat)
		logging.debug(user)

	@_happyEngBot.event
	async def on_successful_payment(
			payment: SuccessfulPayment,
			) -> None:
		logging.debug(_('SUCCESSFUL_PAYMENT').ljust(70, '='))
		logging.debug(payment)


async def _StartBot() -> None:
	from bale.error import NetworkError
	async with _happyEngBot:
		try:
			await _happyEngBot.connect()
		except NetworkError:
			pass


def BotMain() -> None:
	"""The entry point of the Bot."""
	# Declaring variables ---------------------------------
	import asyncio
	from logger import ConfigureLogging
	global _happyEngBot
	global botVars
	# Starting point --------------------------------------
	ConfigureLogging(_APP_DIR / 'log.log')
	_LoadConfig()
	_LoadDatabase()
	_LoadPagesWizards()
	_DoOtherInit()
	_CreateBot()
	# Running the bot...
	try:
		asyncio.run(_StartBot())
	except KeyboardInterrupt:
		asyncio.create_task(_happyEngBot.close())
	except SystemExit:
		asyncio.create_task(_happyEngBot.close())
	finally:
		botVars.pUsers.Clear()
		botVars.db.Close()


if __name__ == '__main__':
	BotMain()


# See https://docs.python-bale-bot.ir/en/stable/event.html
# to get more information about events!
