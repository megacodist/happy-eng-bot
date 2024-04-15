#
# 
#

import logging
from typing import Any, Coroutine

from bale import InlineKeyboardButton, InlineKeyboardMarkup, Message

from . import AbsWizard, Page, WizardRes
import lang as strs
import lang.cmds.cmds1 as cmds1_strs
from utils.types import ID, UserPool


pUsers: UserPool


def InitializeModule(*, user_pool: UserPool) -> None:
    """Initializes the module."""
    global pUsers
    pUsers = user_pool


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

    CONFIRM_CBD = '10'

    RESTART_CBD = '11'

    def __init__(self, bale_id: ID) -> None:
        """Initializes a new instance of the sign-in operation with the
        Bale ID of the user.
        """
        super().__init__()
        self._baleId = bale_id
        """The ID of user in the Bale."""
        self._firstName: str | None = None
        self._lastName: str | None = None
        self._phone: str | None = None

    def Start(self) -> Coroutine[Any, Any, Message]:
        return self.Reply(
            pUsers[self._baleId].GetFirstInput().bale_msg,
            cmds1_strs.SIGN_IN_ENTER_FIRST_NAME)

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
                    cmds1_strs.SIGN_IN_ENTER_LAST_NAME,
                    components=buttons),
                False)
        elif self._lastName is None:
            self._lastName = pUsers[self._baleId].GetFirstInput().data
            self._AppendRestartBtn(buttons)
            return WizardRes(
                self.Reply(
                    pUsers[self._baleId].GetFirstInput().bale_msg.reply,
                    cmds1_strs.SIGN_IN_ENTER_PHONE,
                    components=buttons),
                False)
        elif self._phone is None:
            # Saving data to 'phone'...
            self._phone = pUsers[self._baleId].GetFirstInput().data
            # Confirming all data...
            buttons.add(InlineKeyboardButton(
                strs.CONFIRM,
                callback_data=f'{self.CONFIRM_CBD}'))
            buttons.add(InlineKeyboardButton(
                strs.RESTART,
                callback_data=f'{self.RESTART_CBD}'))
            response = '{0}\n{1}: {2}\n{3}: {4}\n{5}: {6}'.format(
                strs.CONFIRM_DATA,
                cmds1_strs.FIRST_NAME,
                self._firstName,
                cmds1_strs.LAST_NAME,
                self._lastName,
                cmds1_strs.PHONE,
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

    def ReplyCallback(
            self,
            bale_msg: Message,
            cb_data: str,
            ) -> WizardRes:
        match cb_data:
            case self.CONFIRM_CBD:
                self._userPool[self._baleId] = UserData(
                    self._baleId,
                    self._firstName,
                    self._lastName,
                    self._phone)
                return WizardRes(self.Reply(None), True,)
            case self.RESTART_CBD:
                self._firstName = None
                self._lastName = None
                self._phone = None
                return WizardRes(self.Reply(self.Start, bale_msg), False,)
            case _:
                logging.error(f'{cb_data}: unknown callback in '
                    f'{self.__class__.__qualname__}')
                return WizardRes(None, False,)
    
    def _AppendRestartBtn(self, buttons: InlineKeyboardMarkup) -> None:
        """Appends 'Restart' button to the `buttons`."""
        buttons.add(InlineKeyboardButton(
            lang.RESTART,
            callback_data=f'{self.RESTART_CBD}'))


