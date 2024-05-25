#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
import gettext
import logging
from msilib.schema import File
from typing import Awaitable, Callable

from bale import InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import ID
import lang as strs
from utils.types import AbsWizard, AbsPage, DomainLang, UserSpace, BotVars


botVars = BotVars()


def GetPages() -> tuple[type[AbsPage], ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple([HelpPage,])


def GetWizards() -> tuple[type[AbsWizard], ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple()


class HelpPage(AbsPage):
    CMD = '/help'

    @classmethod
    def GetDescr(cls, bale_id: ID) -> str:
        global botVars
        return botVars.pDomains.GetStr(bale_id, 'cmds', 'HELP_CMD_DESCR')

    @classmethod
    async def Show(cls, bale_id: ID) -> None:
        """Gets a list of all available commands."""
        # Declaring variables ---------------------------------
        global botVars
        userSpace: UserSpace
        GetStr: Callable[[ID, str, str], str]
        # Functioning -----------------------------------------
        userSpace = botVars.pUsers.GetItemBypass(bale_id)
        GetStr = botVars.pDomains.GetStr
        text = GetStr(bale_id, 'cmds', 'HELP_ALL_CMDS') + '\n' + ('-' * 20)
        if botVars.pages:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.pages[cmd].GetDescr(bale_id)}\n'
                for cmd in botVars.pages)
        if botVars.wizards:
            text += '\n'.join(
                f'{cmd}\n{botVars.wizards[cmd].GetDescr(bale_id)}\n'
                for cmd in botVars.wizards)
        await userSpace.AppendOutput(
            botVars.bot.send_message(
                userSpace.GetFirstInput().bale_msg.chat_id, # type: ignore
                text,))


def LangSelectPage(bale_msg: Message, cbd: str) -> Awaitable[Message]:
    """Asks for prefered language available. `cbd` is the prefix of
    callback data.
    """
    from pathlib import Path
    global botVars
    texts = list[str]()
    buttons = InlineKeyboardMarkup()
    row = 1
    for lang in botVars.langs:
        try:
            gnuTrans = gettext.translation(
                domain='main',
                localedir=botVars.LOCALES_DIR,
                languages=[lang,])
        except OSError as error:
            # Catches OSError and all its subclasses including
            # FileNotFoundError...
            logging.error(
                'E4-3',
                None,
                'main',
                lang,
                exc_info=True,)
        else:
            texts.append(gnuTrans.gettext('SELECT_LANG'))
            buttons.add(
                InlineKeyboardButton(
                    gnuTrans.gettext('LANG'),
                    callback_data=f'{cbd}-{lang}'),
                row,)
            row += 1
    if texts:
        return botVars.bot.send_message(
            bale_msg.chat_id, # type: ignore
            '\n'.join(texts),
            components=buttons)
    else:
        logging.error('E7')
        return botVars.bot.send_message(
            bale_msg.chat_id, # type: ignore
            'An error occurred:\nE7',)
