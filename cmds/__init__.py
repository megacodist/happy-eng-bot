#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
import gettext
import logging
from typing import Awaitable

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
    def GetDescr(cls, lang: str) -> str:
        global botVars
        cmdsTrans = botVars.pDomains.GetItem(DomainLang(lang, 'cmds'))
        _ = cmdsTrans.gettext
        return _('HELP_CMD_DESCR')

    @classmethod
    async def Show(cls, bale_id: ID) -> None:
        """Gets a list of all available commands."""
        # Declaring variables ---------------------------------
        global botVars
        cmdsTrans: gettext.GNUTranslations
        userSpace: UserSpace
        # Functioning -----------------------------------------
        userSpace = botVars.pUsers.GetItemBypass(bale_id)
        cmdsTrans = botVars.pDomains.GetItem(
            DomainLang('cmds', userSpace.dbUser.Lang))
        text = cmdsTrans.gettext('HELP_ALL_CMDS')
        if botVars.pages:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.pages[cmd].GetDescr(
                    userSpace.dbUser.Lang)}\n'
                for cmd in botVars.pages)
        if botVars.wizards:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.wizards[cmd].GetDescr(
                    userSpace.dbUser.Lang)}\n'
                for cmd in botVars.wizards)
        await userSpace.AppendOutput(
            userSpace.GetFirstInput().bale_msg.reply(text))


def LangSelectPage(bale_msg: Message) -> Awaitable[Message]:
    """Asks for prefered language available."""
    from pathlib import Path
    global botVars
    texts = list[str]()
    buttons = InlineKeyboardMarkup()
    row = 1
    for item in Path(botVars.localDir).iterdir():
        if item.is_dir():
            gnuTrans = gettext.translation(
                domain='main',
                localedir=botVars.localDir,
                languages=[item.name])
            _ = gnuTrans.gettext
            texts.append(_('SELECT_LANG'))
            buttons.add(
                InlineKeyboardButton(
                    _('LANG'),
                    callback_data=f'0-{item.name}'),
                row,)
            row += 1
    if texts:
        return botVars.bot.send_message(
            bale_msg.chat_id, # type: ignore
            '\n'.join(texts),
            components=buttons)
    else:
        logging.error('E7')
        return bale_msg.reply('An error occurred:\nE7')
