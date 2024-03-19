#
#
#
"""This module offers panels for end users depending upon their access
and stage of work.
"""

from typing import Any, Coroutine

from bale import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    MenuKeyboardMarkup, MenuKeyboardButton)

from db import IDatabase
import lang
from utils.types import Commands


COMING_SOON = 'Coming soon...'


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


def GetUnknownReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    """Gets the suitable response for an unknown command."""
    text = lang.UNKNOWN_COMMAND.format(message.text)
    buttons = InlineKeyboardMarkup()
    _GetCommandInfoButton(Commands.HELP ,text, buttons)
    return message.reply(text, components=buttons)


def GetAdminReply(
        message: Message | None,
        admin_ids: tuple[int, ...]
        ) -> Coroutine[Any, Any, Message]:
    """Responds the message with the admin panel. Parameters are as
    follow:
    * `message`: the end user.
    * `admin_ids`: the IDs of all admin users.
    """
    if message.from_user is None or message.from_user.id not in admin_ids:
        # Prompting no access...
        return message.reply(lang.ADMIN_PANEL_NO_ACCESS)
    else:
        # Prompting admin panel...
        text = lang.ADMIN_PANEL
        return message.reply(text)


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
    text += f'\n\n{Commands.PRODUCTS.value}'
    text = _GetCommandInfoButton(Commands.PRODUCTS, text, buttons)
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
