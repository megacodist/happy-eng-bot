#
# 
#

import gettext
import logging

from bale import InlineKeyboardButton, InlineKeyboardMarkup

import lang.cmds.basic as basic_strs
from utils.types import (
    AbsPage, AbsWizard, DomainLang, BotVars, ID, TextInput, UserSpace,
    WizardRes)


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
        cmdsTrans = botVars.pDomains.GetItem(DomainLang('cmds_basic', lang))
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

    async def Start(self) -> WizardRes:
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        self._firstName = userSpace.dbUser._firstName
        self._lastName = userSpace.dbUser._lastName
        self._phone = userSpace.dbUser._phone
        if self._firstName and self._lastName and self._phone:
            return await self._Confirm()
        else:
            basicTrans = botVars.pDomains.GetItem(
                DomainLang('cmds_basic', userSpace.dbUser.Lang))
            _ = basicTrans.gettext
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    _('SIGN_IN_ENTER_FIRST_NAME')),
                False,)

    async def ReplyText(self) -> WizardRes:
        """Gets from user and fills folowing items in consecutive calls:
        1. first name
        2. last name
        3. e-mail
        4. phone no.
        """
        # Declaring variables -----------------------------
        global botVars
        basicTrans: gettext.GNUTranslations
        # Processing input --------------------------------
        lastInput = botVars.pUsers[self._baleId].GetFirstInput()
        if not isinstance(lastInput, TextInput):
            logging.error('E3-2', stack_info=True)
            return WizardRes(None, False)
        buttons = InlineKeyboardMarkup()
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        basicTrans = botVars.pDomains.GetItem(
            DomainLang('cmds_basic', userSpace.dbUser.Lang))
        _ = basicTrans.gettext
        if self._firstName is None:
            self._firstName = lastInput.text
            buttons.add(self._GetRestartBtn())
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    _('SIGN_IN_ENTER_LAST_NAME'),
                    components=buttons),
                False)
        elif self._lastName is None:
            self._lastName = lastInput.text
            buttons.add(self._GetRestartBtn())
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    _('SIGN_IN_ENTER_PHONE'),
                    components=buttons),
                False)
        elif self._phone is None:
            # Saving data to 'phone'...
            self._phone = lastInput.text
            # Confirming all data...
            return await self._Confirm()
        else:
            logging.error('E3-1', stack_info=True)
            return WizardRes(None, False,)

    async def ReplyCallback(self) -> WizardRes:
        # Declaring variables -----------------------------
        from utils.types import CbInput
        global botVars
        gnuTrans: gettext.GNUTranslations
        # Replying ----------------------------------------
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        lastInput = userSpace.GetFirstInput()
        if not isinstance(lastInput, CbInput):
            logging.error('E3-3', stack_info=True)
            return WizardRes(None, False)
        match lastInput.cb:
            case self._CONFIRM_CBD:
                userSpace.dbUser.FirstName = self._firstName # type:ignore
                userSpace.dbUser.LastName = self._lastName # type:ignore
                userSpace.dbUser.Phone = self._phone # type:ignore
                return WizardRes(self.Reply(None), True,)
            case self._RESTART_CBD:
                self._firstName = None
                self._lastName = None
                self._phone = None
                return await self.Start()
            case _:
                logging.error(f'{lastInput.cb}:')
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
