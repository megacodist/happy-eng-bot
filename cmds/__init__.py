#
# 
#
"""This package ABCs and implementation of Bot commands."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from bale import Message

from db import ID
from utils.types import AbsWizard, Page, PgCallback, UserPool


# ===================================================================
# Bot-wide variables ================================================
# ===================================================================
pUsers: UserPool

pages: dict[str, PgCallback]

wizards: dict[str, AbsWizard]


# ===================================================================
# Functions =========================================================
# ===================================================================
def InitModule(
        *,
        pages_: dict[str, PgCallback],
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


def GetPages() -> tuple[Page, ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple([Page('/help', GetHelpPg)])


def GetWizards() -> tuple[AbsWizard, ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple()


def GetHelpPg(id: ID) -> Coroutine[Any, Any, Message]:
    """Gets a list of all available commands."""
    # Declaring variables ---------------------------------
    import lang as strs
    global pUsers
    global pages
    global wizards
    # Functioning -----------------------------------------
    text = strs.HELP_ALL_CMDS
    text += '\n' + '\n'.join(cmd for cmd in pages)
    text += '\n' + '\n'.join(cmd for cmd in wizards)
    return pUsers[id].GetFirstInput().bale_msg.reply(text)
