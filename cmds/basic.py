#
# 
#

import logging
from typing import Any, Callable, Coroutine

from bale import InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import UserData
import lang as strs
import lang.cmds.basic as basic_strs
from utils.types import AbsWizard, ID, Page, PgCallback, UserPool, WizardRes


# Bot-wide variables ================================================
pUsers: UserPool

pages: dict[str, Callable[[ID], Coroutine[Any, Any, Message]]]

wizards: dict[str, AbsWizard]


def InitModule(
        *,
        pUsers_: UserPool,
        pages_: dict[str, PgCallback],
        wizards_: dict[str, AbsWizard],
        **kwargs
        ) -> None:
    """Initializes Bot-wide variables of this module."""
    global pUsers
    global pages
    global wizards
    pUsers = pUsers_
    pages = pages_
    wizards = wizards_


def GetPages() -> tuple[Page, ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple()


def GetWizards() -> tuple[AbsWizard, ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple([SigninWiz,])


class SigninWiz(AbsWizard):
    """Encapsulates a sign-in operation in the Bot. You should start
    this operation by calling `Start` method.
    """
    CMD = '/signin'

    _CONFIRM_CBD = '10'

    _RESTART_CBD = '11'

    def __init__(self, bale_id: ID, uwid: int) -> None:
        """Initializes a new instance of the sign-in operation with the
        Bale ID of the user.
        """
        super().__init__(bale_id, uwid)
        self._baleId = bale_id
        """The ID of user in the Bale."""
        self._firstName: str | None = None
        self._lastName: str | None = None
        self._phone: str | None = None

    def Start(self) -> Coroutine[Any, Any, Message]:
        return self.Reply(
            pUsers[self._baleId].GetFirstInput().bale_msg.reply,
            basic_strs.SIGN_IN_ENTER_FIRST_NAME)

    def ReplyText(self) -> WizardRes:
        """Gets from user and fills folowing items in consecutive calls:
        1. first name
        2. last name
        3. e-mail
        4. phone no.
        """
        buttons = InlineKeyboardMarkup()
        if self._firstName is None:
            self._firstName = pUsers[self._baleId].GetFirstInput().data
            self._AppendRestartBtn(buttons)
            return WizardRes(
                self.Reply(
                    pUsers[self._baleId].GetFirstInput().bale_msg.reply,
                    basic_strs.SIGN_IN_ENTER_LAST_NAME,
                    components=buttons),
                False)
        elif self._lastName is None:
            self._lastName = pUsers[self._baleId].GetFirstInput().data
            self._AppendRestartBtn(buttons)
            return WizardRes(
                self.Reply(
                    pUsers[self._baleId].GetFirstInput().bale_msg.reply,
                    basic_strs.SIGN_IN_ENTER_PHONE,
                    components=buttons),
                False)
        elif self._phone is None:
            # Saving data to 'phone'...
            self._phone = pUsers[self._baleId].GetFirstInput().data
            # Confirming all data...
            buttons.add(InlineKeyboardButton(
                strs.CONFIRM,
                callback_data=f'{self._CONFIRM_CBD}'))
            buttons.add(InlineKeyboardButton(
                strs.RESTART,
                callback_data=f'{self._RESTART_CBD}'))
            response = '{0}\n{1}: {2}\n{3}: {4}\n{5}: {6}'.format(
                strs.CONFIRM_DATA,
                basic_strs.FIRST_NAME,
                self._firstName,
                basic_strs.LAST_NAME,
                self._lastName,
                basic_strs.PHONE,
                self._phone)
            return WizardRes(
                self.Reply(
                    pUsers[self._baleId].GetFirstInput().bale_msg.reply,
                    response,
                    components=buttons),
                False,)
        else:
            logging.error('E1-3')
            return WizardRes(None, False,)

    def ReplyCallback(self) -> WizardRes:
        global pUsers
        match pUsers[self._baleId].GetFirstInput().data:
            case self._CONFIRM_CBD:
                pUsers[self._baleId].dbUser = UserData(
                    self._baleId,
                    self._firstName,
                    self._lastName,
                    self._phone)
                return WizardRes(self.Reply(None), True,)
            case self._RESTART_CBD:
                self._firstName = None
                self._lastName = None
                self._phone = None
                return WizardRes(self.Reply(self.Start), False,)
            case _:
                logging.error(f'{pUsers[self._baleId].GetFirstInput().data}:'
                    f' unknown callback in {self.__class__.__qualname__}')
                return WizardRes(None, False,)
    
    def _Confirm(self) -> WizardRes:
        pair = '{}: {}'
        text = strs.CONFIRM_DATA
        text += '\n' + pair.format(basic_strs.FIRST_NAME, self._firstName)
        text += '\n' + pair.format(basic_strs.LAST_NAME, self._lastName)
        text += '\n' + pair.format(basic_strs.PHONE, self._phone)
        return WizardRes(
            self.Reply(
                pUsers.GetItemBypass(
                    self._baleId).GetFirstInput().bale_msg.reply,
                text,),
            False,)
    
    def _AppendRestartBtn(self, buttons: InlineKeyboardMarkup) -> None:
        """Appends 'Restart' button to the `buttons`."""
        buttons.add(InlineKeyboardButton(
            strs.RESTART,
            callback_data=f'{self._RESTART_CBD}'))


