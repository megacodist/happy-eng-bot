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
from utils.types import Commands, UserPool, OperationPool


COMING_SOON = 'Coming soon...'


def _GetCommandInfoButton(
        cmd: Commands,
        text: str | None = None,
        buttons: InlineKeyboardMarkup | None = None,
        ) -> str | None:
    """Gets information and button related to command. Firstly
    it adds a button to the `buttons`, if available, and then it
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
        bale_msg: Message | None,
        cmd: str,
        ) -> Coroutine[Any, Any, Message]:
    """Informs the user that the command is unexpected. It also shows
    'Help' button for acceptable commands.
    """
    text = lang.UNEX_CMD.format(cmd)
    buttons = InlineKeyboardMarkup()
    _GetCommandInfoButton(Commands.HELP ,text, buttons)
    return bale_msg.reply(text, components=buttons)


def GetUnexDataReply(
        bale_msg: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return bale_msg.reply(lang.UNEX_DATA)


def GetAdminReply(
        bale_msg: Message | None,
        bale_user: User,
        admin_ids: tuple[int, ...]
        ) -> Coroutine[Any, Any, Message]:
    """Responds the message with the admin panel. Parameters are as
    follow:
    * `message`: the end user.
    * `admin_ids`: the IDs of all admin users.
    """
    if bale_user is None or bale_user.id not in admin_ids:
        # Prompting no access...
        return bale_msg.reply(lang.ADMIN_PANEL_NO_ACCESS)
    else:
        # Prompting admin panel...
        text = lang.ADMIN_PANEL
        return bale_msg.reply(text)


def GetHelpReply(
        bale_msg: Message | None,
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
    return bale_msg.reply(text, components=buttons)


def GetShowcaseReply(
        bale_msg: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    return bale_msg.reply(COMING_SOON)


def GetStartReply(
        bale_msg: Message | None,
        bale_user: User,
        user_pool: UserPool,
        admin_ids: tuple[int, ...],
        ) -> Coroutine[Any, Any, Message]:
    # Rejecting unknown users...
    if bale_user.id is None:
        return bale_msg.reply(lang.UNKNOWN_USER)
    # Sign in/My courses...
    buttons = InlineKeyboardMarkup()
    text = lang.START
    if bale_user.id in admin_ids:
        _GetCommandInfoButton(Commands.ADMIN, text=None, buttons=buttons)
    elif bale_user.id in user_pool:
        _GetCommandInfoButton(Commands.MY_COURSES, None, buttons)
    else:
        _GetCommandInfoButton(Commands.SIGN_IN, None, buttons)
    return bale_msg.reply(
        text,
        components=buttons)


def GetSiginReply(
        message: Message | None,
        bale_user: User,
        user_pool: UserPool,
        op_pool: OperationPool,
        ) -> Coroutine[Any, Any, Message]:
    # Reading user from database...
    try:
        userData = user_pool[bale_user.id]
    except KeyError:
        userData = None
    # Checking if user already signed in...
    if userData:
        buttons = InlineKeyboardMarkup()
        buttons.add(InlineKeyboardButton(
            text=lang.START,
            callback_data=Commands.START.value))
        return message.reply(
            text=lang.ALREADY_SIGNED_IN,
            components=buttons)
    # Initiating sign in operation...
    from utils.types import SigninOp
    siginOp = SigninOp(bale_user.id, user_pool)
    op_pool[bale_user.id] = siginOp
    return siginOp.Start(message)
