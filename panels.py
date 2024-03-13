#
#
#
"""This module offers panels for end users depending upon their access
and stage of work.
"""


from asyncio import coroutines
from typing import Any, Coroutine

from bale import Message

import lang
from utils.types import Language


def RejectUnknownUser(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    """Rejects the message from an unknown user."""
    return message.reply(lang.REJECT_UNKNOWN)


def GetNewcomerReply(
        message: Message | None,
        ) -> Coroutine[Any, Any, Message]:
    """Responds the message with the newcomer panel."""
    # Declaring variables ---------------------------------
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    # Responding ------------------------------------------
    text = '\n'.join(langs[lang].messages['SELECT_LANG'] for lang in langs)
    components = InlineKeyboardMarkup()
    for lang in langs:
        components.add(InlineKeyboardButton(langs[lang].names['LANG']))
    return message.reply(text, components=components)


def GetReply(
        message: Message,
        intro: bool = False,
        ) -> Coroutine[Any, Any, Message]:
    aaa = []


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
        pass
    else:
        # Prompting admin panel...
        message.reply('Coming soon...')
