#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
import gettext
import logging
from msilib.schema import File
from typing import Awaitable, Callable, Generator

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
    global botVars
    texts = list[str]()
    buttons = InlineKeyboardMarkup()
    for row, langSelect in enumerate(IterLangs(scan=True), 1):
        texts.append(langSelect.selectMsg)
        buttons.add(
            InlineKeyboardButton(
                text=langSelect.langName,
                callback_data=f'{cbd}-{langSelect.langCode}'),
            row)
    if texts:
        return botVars.bot.send_message(
            bale_msg.chat_id, # type: ignore
            '\n'.join(texts),
            components=buttons)
    else:
        logging.error('E4-4', None, stack_info=True)
        return botVars.bot.send_message(
            bale_msg.chat_id, # type: ignore
            'An error occurred:\nE7',)


class LangSelect:
    """This struct packs language code, language name, and a message for
    selecting the language.
    """
    def __init__(
            self,
            lang_code: str,
            lang_name: str,
            select_msg: str,
            ) -> None:
        self.langCode = lang_code
        self.langName = lang_name
        self.selectMsg = select_msg


def IterLangs(scan: bool = False) -> Generator[LangSelect, None, None]:
    """Iterates over installed languages and yields each language code
    along with a message to select them packed as a `LangSelect` struct.
    `scan` flag specifies whether to scan for installed languages
    beforehand.
    """
    # Declaring variables ---------------------------------
    global botVars
    # Iterating over installed languages ------------------
    if scan:
        botVars.GetLangs()
    for langCode in botVars.langs:
        try:
            gnuTrans = botVars.pDomains.GetItem(DomainLang('main', langCode))
        except OSError as error:
            # Catches OSError and all its subclasses including
            # FileNotFoundError...
            logging.error(
                'E4-3',
                None,
                'main',
                langCode,
                exc_info=True,)
        else:
            langName = gnuTrans.gettext('LANG')
            if langName == 'LANG':
                logging.error(
                    'E4-2',
                    None,
                    'LANG',
                    'main',
                    langCode,
                    stack_info=True)
            selectMsg = gnuTrans.gettext('SELECT_LANG')
            if selectMsg == 'SELECT_LANG':
                logging.error(
                    'E4-2',
                    None,
                    'SELECT_LANG',
                    'main',
                    langCode,
                    stack_info=True)
            yield LangSelect(langCode, langName, selectMsg)
