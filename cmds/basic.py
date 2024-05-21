#
# 
#

from dbm import gnu
import gettext
import logging
from typing import Any, Callable, Coroutine

from bale import InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import UserData
import lang as strs
import lang.cmds.basic as basic_strs
from utils.types import (
    AbsPage, AbsWizard, DomainLang, BotVars, ID, UserSpace, WizardRes)


# Bot-wide variables ================================================
botVars = BotVars()


def GetPages() -> tuple[type[AbsPage], ...]:
    """Gets a tuple of all implemented `Page`s in this module."""
    return tuple()


def GetWizards() -> tuple[type[AbsWizard], ...]:
    """Gets a tuple of all implemented `Wizard`s in this module."""
    return tuple([SigninWiz,])


class SigninWiz(AbsWizard):
    """Encapsulates a sign-in operation in the Bot. You should start
    this operation by calling `Start` method.
    """
    CMD = '/signin'

    DESCR = basic_strs.SIGNIN_INTRO

    _CONFIRM_CBD = '10'

    _RESTART_CBD = '11'

    @classmethod
    def GetDescr(cls, lang: str) -> str:
        global botVars
        cmdsTrans = botVars.pDomains.GetItem(DomainLang(lang, 'cmds_basic'))
        _ = cmdsTrans.gettext
        return _('SIGNIN_CMD_DESCR')

    def __init__(self, bale_id: ID, uwid: str) -> None:
        """Initializes a new instance of the sign-in operation with the
        Bale ID of the user.
        """
        super().__init__(bale_id, uwid)
        self._baleId = bale_id
        """The ID of user in the Bale."""
        self._firstName: str | None = None
        self._lastName: str | None = None
        self._phone: str | None = None

    async def Start(self) -> Coroutine[Any, Any, Message]:
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        self._firstName = userSpace.dbUser._firstName
        self._lastName = userSpace.dbUser._lastName
        self._phone = userSpace.dbUser._phone
        if self._firstName and self._lastName and self._phone:
            await self._Confirm()
        else:
            return self.Reply(
                pUsers[self._baleId].GetFirstInput().bale_msg.reply,
                basic_strs.SIGN_IN_ENTER_FIRST_NAME)

    async def ReplyText(self) -> WizardRes:
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

    async def ReplyCallback(self) -> WizardRes:
        # Declaring variables -----------------------------
        from utils.types import CbInput
        global botVars
        gnuTrans: gettext.GNUTranslations
        #  -------------------------
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        input_: CbInput = userSpace.GetFirstInput() # type: ignore
        match input_.cb:
            case self._CONFIRM_CBD:
                userSpace.dbUser = UserData(
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
    
    async def _Confirm(self) -> WizardRes:
        # Declaring variables -----------------------------
        global botVars
        gnuTrans: gettext.GNUTranslations
        userSpace: UserSpace
        # Asking for confirmation -------------------------
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        gnuTrans = botVars.pDomains.GetItem(
            DomainLang('cmds_basic', userSpace.dbUser.Lang))
        _ = gnuTrans.gettext
        pair = '{}: {}'
        text = _('ASK_CONFIRMATION')
        text += '\n' + pair.format(_('FIRST_NAME'), self._firstName)
        text += '\n' + pair.format(_('LAST_NAME'), self._lastName)
        text += '\n' + pair.format(_('PHONE'), self._phone)
        buttons = InlineKeyboardMarkup()
        buttons.add(self._GetConfirmBtn())
        buttons.add(self._GetRestartBtn())
        return WizardRes(
            self.Reply(
                botVars.pUsers.GetItemBypass(
                    self._baleId).GetFirstInput().bale_msg.reply,
                text,
                components=buttons,),
            False,)
    
    def _GetRestartBtn(self) -> InlineKeyboardButton:
        """Gets 'Restart' button."""
        global botVars
        gnuTrans = botVars.pDomains.GetItem(DomainLang(
            'cmds',
            botVars.pUsers.GetItemBypass(self._baleId).dbUser.Lang))
        _ = gnuTrans.gettext
        return InlineKeyboardButton(
            _('RESTART'),
            callback_data=f'{self.Uwid}-{self._RESTART_CBD}')

    def _GetConfirmBtn(self) -> InlineKeyboardButton:
        global botVars
        gnuTrans = botVars.pDomains.GetItem(DomainLang(
            'cmds',
            botVars.pUsers.GetItemBypass(self._baleId).dbUser.Lang))
        _ = gnuTrans.gettext
        return InlineKeyboardButton(
            _('CONFIRM'),
            callback_data=f'{self.Uwid}-{self._CONFIRM_CBD}')
