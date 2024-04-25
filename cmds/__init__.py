#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from bale import Message

from db import ID
import lang as strs
from utils.types import AbsWizard, AbsPage, UserPool, UserSpace


# ===================================================================
# Bot-wide variables ================================================
# ===================================================================
pUsers: UserPool

pages: dict[str, AbsPage]

wizards: dict[str, AbsWizard]


# ===================================================================
# Functions =========================================================
# ===================================================================
def InitModule(
        *,
        pages_: dict[str, AbsPage],
        wizards_: dict[str, AbsWizard],
        pUsers_: UserPool,
        **kwargs
        ) -> None:
    """Initializes the module.""" 
    global pages
    global wizards
    global pUsers
    pages = pages_
    wizards = wizards_
    pUsers = pUsers_


def GetPages() -> tuple[AbsPage, ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple([HelpPage,])


def GetWizards() -> tuple[AbsWizard, ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple()


class HelpPage(AbsPage):
    CMD = '/help'

    DESCR = strs.HELP_CMD_INTRO

    @classmethod
    async def Show(self, bale_id: ID) -> Coroutine[Any, Any, None]:
        """Gets a list of all available commands."""
        # Declaring variables ---------------------------------
        import lang as strs
        global pUsers
        global pages
        global wizards
        userSpace: UserSpace
        # Functioning -----------------------------------------
        userSpace = pUsers.GetItemBypass(bale_id)
        text = strs.HELP_ALL_CMDS
        if pages:
            text += '\n' + '\n'.join(
                f'{cmd}\n{pages[cmd].DESCR}\n'
                for cmd in pages)
        if wizards:
            text += '\n' + '\n'.join(
                f'{cmd}\n{wizards[cmd].DESCR}\n'
                for cmd in wizards)
        return await userSpace.AppendOutput(
            userSpace.GetFirstInput().bale_msg.reply(text))


def GetHelpPg(id: ID) -> Coroutine[Any, Any, Message]:
    """Gets a list of all available commands."""
    # Declaring variables ---------------------------------
    import lang as strs
    global pUsers
    global pages
    global wizards
    # Functioning -----------------------------------------
    text = strs.HELP_ALL_CMDS
    if pages:
        text += '\n' + '\n'.join(cmd for cmd in pages)
    if wizards:
        text += '\n' + '\n'.join(cmd for cmd in wizards)
    return pUsers[id].GetFirstInput().bale_msg.reply(text)
