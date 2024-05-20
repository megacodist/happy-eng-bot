#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
import gettext
from typing import Any, Callable, Coroutine, TYPE_CHECKING

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
            DomainLang(userSpace.dbUser.Lang, 'cmds'))
        text = cmdsTrans.gettext('HELP_ALL_CMDS')
        if botVars.pages:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.pages[cmd].GetDescr(
                    userSpace.dbUser.Lang)}\n'
                for cmd in botVars.pages)
        if botVars.wizards:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.wizards[cmd].DESCR}\n'
                for cmd in botVars.wizards)
        await userSpace.AppendOutput(
            userSpace.GetFirstInput().bale_msg.reply(text))


class LangSelectPage(AbsPage):
    CMD = '/lang'

    @classmethod
    def GetDescr(cls, lang: str) -> str:
        global botVars
        cmdsTrans = botVars.pDomains.GetItem(DomainLang(lang, 'cmds'))
        _ = cmdsTrans.gettext
        return _('LANG_CMD_DESCR')
    
    @classmethod
    async def Show(cls, bale_id: ID) -> None:
        from pathlib import Path
        global botVars
        text = ''
        buttons = InlineKeyboardMarkup()
        for item in Path(botVars.localDir).iterdir():
            if item.is_dir():
                gnuTrans = botVars.pDomains.GetItem(
                    DomainLang('main', item.name))
                _ = gnuTrans.gettext
                text += _('SELECT_LANG')
                buttons.add(InlineKeyboardButton(
                    _('LANG'),
                    callback_data=f'0-{item.name}'))
