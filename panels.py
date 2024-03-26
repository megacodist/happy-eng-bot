#
#
#
"""This module offers panels for end users depending upon their access
and stage of work.
"""

from typing import Any, Coroutine

from bale import (
    Message, User, InlineKeyboardMarkup, InlineKeyboardButton,
    MenuKeyboardMarkup, MenuKeyboardButton)

from db import IDatabase
import lang
from utils.types import AbsOperation, AutoDelObj, Commands, SDelPool


COMING_SOON = 'Coming soon...'


async def _GetSignInInfo(
        message: Message,
        obj: AutoDelObj,
        text: str,
        ) -> Coroutine[Any, Any, None]:
    """Accepts and object and adds `text` as follwoing attributes in
    consecutive calls:
    1. `firstName`: the first name
    2. `lastName`: the last (family) name
    3. `email`: the e-mail address
    4. `phone`: the phone no.
    """
    # Setting first name...
    try:
        obj.firstName
    except AttributeError:
        await message.reply(lang.ENTER_YOUR_FIRST_NAME)
        obj.firstName = text
        return
    # Setting last name...
    try:
        obj.lastName
    except AttributeError:
        obj.lastName = text
        return
    # Setting last name...
    try:
        obj.email
    except AttributeError:
        obj.email = text
        return
    # Setting last name...
    try:
        obj.email
    except AttributeError:
        obj.email = text
        return


def _GetCommandInfoButton(
        cmd: Commands,
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to `Products` command. Firstly
    it adds `Products` button to the `buttons`, if available, and then it
    adds information on a new line of `text`, if provided, and returns it.
    """
    # Getting info of the command...
    if text:
        info = getattr(lang, f'{cmd.name}_CMD_INTRO')
        text += f'\n{info}'
    if buttons:
        name = getattr(lang, cmd.name)
        buttons.add(InlineKeyboardButton(
            name,
            callback_data=cmd.value))
    return text


def GetUnexCommandReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    """Gets the suitable response for an unexpected command."""
    text = lang.UNEX_CMD.format(message.text)
    buttons = InlineKeyboardMarkup()
    _GetCommandInfoButton(Commands.HELP ,text, buttons)
    return message.reply(text, components=buttons)


def GetUnexDataReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return message.reply(lang.UNEX_DATA)


def GetAdminReply(
        message: Message | None,
        user: User,
        admin_ids: tuple[int, ...]
        ) -> Coroutine[Any, Any, Message]:
    """Responds the message with the admin panel. Parameters are as
    follow:
    * `message`: the end user.
    * `admin_ids`: the IDs of all admin users.
    """
    if user is None or user.id not in admin_ids:
        # Prompting no access...
        return message.reply(lang.ADMIN_PANEL_NO_ACCESS)
    else:
        # Prompting admin panel...
        text = lang.ADMIN_PANEL
        return message.reply(text)


def GetSigninReply(
        message: Message | None,
        user: User,
        admin_ids: tuple[int, ...],
        db: IDatabase,
        operations: SDelPool[AbsOperation],
        ) -> Coroutine[Any, Any, Message]:
    pass


def GetHelpReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    text: str
    buttons = InlineKeyboardMarkup()
    # Help command...
    text = Commands.HELP.value
    text = _GetCommandInfoButton(Commands.HELP, text, buttons)
    # Start command...
    text += f'\n\n{Commands.START.value}'
    text = _GetCommandInfoButton(Commands.START, text, buttons)
    # Products command...
    text += f'\n\n{Commands.SHOWCASE.value}'
    text = _GetCommandInfoButton(Commands.SHOWCASE, text, buttons)
    return message.reply(text, components=buttons)


def GetProductsReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return message.reply(COMING_SOON)


def GetUserPanelReply(
        message: Message | None,
        db: IDatabase,
        admin_ids: tuple[int, ...],
        ) -> Coroutine[Any, Any, Message]:
    buttons = InlineKeyboardMarkup()
    if message.from_user is None:
        return message.reply(lang.UNKNOWN_USER)
    # Sign in/My courses...
    print('User:', message.from_user)
    text = lang.START
    if message.from_user.id in admin_ids:
        _GetCommandInfoButton(Commands.ADMIN, text=None, buttons=buttons)
    elif db.DoesIdExist(message.from_user.id):
        _GetCommandInfoButton(Commands.MY_COURSES, None, buttons)
    else:
        _GetCommandInfoButton(Commands.SIGN_IN, None, buttons)
    return message.reply(
        text,
        components=buttons)
