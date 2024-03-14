#
#
#
"""This module offers panels for end users depending upon their access
and stage of work.
"""


import enum
from typing import Any, Coroutine, Literal

from bale import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    MenuKeyboardMarkup, MenuKeyboardButton)

import app_utils
from db import IDatabase
import lang


COMING_SOON = 'Coming soon...'


class Commands(enum.Enum):
    HELP


def _GetHelpInfoButton(
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to `Help` command. Firstly
    it adds `Help` button to the `buttons`, if available, and then it
    adds information on a new line of `text`, if provided, and returns it.
    """
    if text:
        text += f'\n{lang.HELP_CMD_INFO}'
    if buttons:
        buttons.add(InlineKeyboardButton(
            lang.HELP,
            callback_data=app_utils.HELP_CMD))
    return text


def _GetStartInfoButton(
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to `Start` command. Firstly
    it adds `Start` button to the `buttons`, if available, and then it
    adds information on a new line of `text`, if provided, and returns it.
    """
    if text:
        text += f'\n{lang.START_CMD_INFO}'
    if buttons:
        buttons.add(InlineKeyboardButton(
            lang.START,
            callback_data=app_utils.START_CMD))
    return text


def _GetProductsInfoButton(
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to `Products` command. Firstly
    it adds `Products` button to the `buttons`, if available, and then it
    adds information on a new line of `text`, if provided, and returns it.
    """
    if text:
        text += f'\n{lang.PROCUDTS_CMD_INFO}'
    if buttons:
        buttons.add(InlineKeyboardButton(
            lang.PRODUCTS,
            callback_data=app_utils.PRODUCTS_CMD))
    return text


def _GetCommandInfoButton(
        cmd: Literal['HELP', 'START', 'PRODUCTS', 'SIGNIN'],
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to `Products` command. Firstly
    it adds `Products` button to the `buttons`, if available, and then it
    adds information on a new line of `text`, if provided, and returns it.
    """
    if text:
        text += f'\n{lang.PROCUDTS_CMD_INFO}'
    if buttons:
        buttons.add(InlineKeyboardButton(
            lang.PRODUCTS,
            callback_data=app_utils.PRODUCTS_CMD))
    return text


def GetUnknownReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    """Gets the suitable response for an unknown command."""
    text = lang.UNKNOWN_COMMAND.format(message.text)
    buttons = InlineKeyboardMarkup()
    _GetHelpInfoButton(text, buttons)
    return message.reply(text, components=buttons)


def GetUserPanelReply(
        message: Message | None,
        db: IDatabase,
        admin_ids: tuple[int, ...],
        ) -> Coroutine[Any, Any, Message]:
    buttons = InlineKeyboardMarkup()
    #
    if message.from_user:
        _G


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
        return message.reply(COMING_SOON)


def GetCommandsReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    text: str
    buttons = InlineKeyboardMarkup()
    # Help command...
    text = app_utils.HELP_CMD
    text = _GetHelpInfoButton(text, buttons)
    # Start command...
    text += f'\n\n{app_utils.START_CMD}'
    text = _GetStartInfoButton(text, buttons)
    # Products command...
    text += f'\n\n{app_utils.PRODUCTS_CMD}'
    text = _GetProductsInfoButton(text, buttons)
    return message.reply(text, components=buttons)


def GetProductsReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return message.reply(COMING_SOON)


def GetUserPanelReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return message.reply(
        COMING_SOON,
        components=MenuKeyboardMarkup().add(MenuKeyboardButton('User')))
