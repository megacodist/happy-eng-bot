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
from db.sqlite3 import SqliteDb
from logger import ConfigureLogging
from panels import (
	GetAdminReply, GetHelpReply, GetShowcaseReply, GetUnexDataReply,
	GetStartReply ,GetUnexCommandReply, GetSiginReply)
from utils.types import (
    Commands, InputType, UserInput, UserPool)


# Bot-wide variables & contants =====================================
_APP_DIR = Path(__file__).resolve().parent
"""The directory of the Bot."""

# Configuring the logger ============================================
ConfigureLogging(_APP_DIR / 'log.log')

# Preparing global variables ========================================
import tomllib
ADMIN_IDS: tuple[int, ...]
"""A tuple of ID's of admin users."""
_TOKEN: str
"""The token of the Bale bot."""
with open(_APP_DIR / 'config.toml', mode='rb') as tomlObj:
	settings = tomllib.load(tomlObj)
	ADMIN_IDS = settings['ADMIN_IDS']
	_TOKEN = settings['BALE_BOT_TOKEN']

db: IDatabase = SqliteDb(_APP_DIR / 'db.db3')
"""The database of the Bot."""

pUsers = UserPool(db)
"""A mapping of `ID -> UserData` contains all information of recent users
of the Bot.
"""

pages: dict[str, Callable] = {}

wizards: dict[str, AbsWizard] = {}

# Loading pages & wizards ===========================================
from importlib import import_module
modsDir = _APP_DIR / 'cmds'
modNames = list(modsDir.glob('*.py'))
try:
	modNames.remove(Path('__init__.py'))
except ValueError:
	pass
botVars = {
	'ADMIN_IDS': ADMIN_IDS,
	'db': db,
	'pUsers': pUsers,}
for modName in modNames:
	modObj = import_module(f'cmds.{modName.stem}')
	try:
		modObj.InitializeModule(**botVars)
		modPages: tuple[Page, ...] = modObj.GetPages()
		modWizards: tuple[AbsWizard, ...] = modObj.GetWizards()
	except Exception:
		logging.error(f'E1-2: {modName.absolute()}')
	else:
		pages.update(modPages)
		wizards.update(modWizards)


# Reply functions =========================================
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
	if inputExists:
		return
	while pUsers[bale_user.id].CountInputs() > 0:
		await pUsers[bale_user.id].ReplyNextInput()


def _DispatchCmd(
		bale_msg: Message,
		bale_user: User,
		cmd: str | None,
		) -> Coroutine[Any, Any, Message] | None:
	# Checking interference with an ongoing operation...
	try:
		return opPool.CancelByCmdReply(bale_msg, bale_user, cmd)
	except (KeyError, ValueError):
		pass
	# Initiating a new operation...
	cmdParts = cmd.split()
	cmdParts[0] = cmdParts[0].lower()
	match cmdParts[0]:
		case Commands.ADMIN.value:
			return GetAdminReply(bale_msg, ADMIN_IDS)
		case Commands.HELP.value:
			return GetHelpReply(bale_msg)
		case Commands.START.value:
			return GetStartReply(
				bale_msg,
				bale_user,
				pUsers,
				ADMIN_IDS)
		case Commands.SHOWCASE.value:
			return GetShowcaseReply(bale_msg)
		case Commands.SIGN_IN.value:
			return GetSiginReply(
				bale_msg,
				bale_user,
				pUsers,
				opPool)
		case Commands.MY_COURSES.value:
			pass
		case _:
			return GetUnexCommandReply(bale_msg, cmd)


opPool._cmdDispatcher = _DispatchCmd


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
	logging.debug(callback)
	if not callback.data:
		logging.info('A callback with no data.')
		return
	await _DispatchInput(
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


def main() -> None:
	# Declaring of variables -----------------
	import asyncio
	task: asyncio.Task | None
	# Local functions ------------------------
	async def _main() -> None:
		async with happyEngBot:
			await happyEngBot.connect()

	try:
		asyncio.run(_main())
	except KeyboardInterrupt:
		asyncio.create_task(happyEngBot.close())
	except SystemExit:
		asyncio.create_task(happyEngBot.close())
	finally:
		pUsers.close()
		db.Close()


if __name__ == '__main__':
	main()


# See https://docs.python-bale-bot.ir/en/stable/event.html
# to get more information about events!
