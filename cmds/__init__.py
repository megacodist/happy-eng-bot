#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, TYPE_CHECKING

from bale import Message

from db import ID
import lang as strs
from utils.types import AbsWizard, AbsPage, DomainLang, UserSpace, BotVars


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda x: x


botVars = BotVars()


def GetPages() -> tuple[type[AbsPage], ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple([HelpPage,])


def GetWizards() -> tuple[type[AbsWizard], ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple()


class HelpPage(AbsPage):
    CMD = '/help'

    def DESCR(self) -> str:
        botVars.pDomains.GetItem(
            DomainLang(
                botVars.pUsers.GetItemBypass(self._baleId).dbUser.Lang,
                'cmds')).install()

    async def Show(self, bale_id: ID) -> None:
        """Gets a list of all available commands."""
        # Declaring variables ---------------------------------
        import lang as strs
        global botVars
        userSpace: UserSpace
        # Functioning -----------------------------------------
        botVars.pDomains.GetItem(
            DomainLang(
                botVars.pUsers.GetItemBypass(bale_id).dbUser.Lang,
                'cmds')).install()
        userSpace = botVars.pUsers.GetItemBypass(bale_id)
        text = _('HELP_ALL_CMDS')
        if botVars.pages:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.pages[cmd].DESCR}\n'
                for cmd in botVars.pages)
        if botVars.wizards:
            text += '\n' + '\n'.join(
                f'{cmd}\n{botVars.wizards[cmd].DESCR}\n'
                for cmd in botVars.wizards)
        await userSpace.AppendOutput(
            userSpace.GetFirstInput().bale_msg.reply(text))
