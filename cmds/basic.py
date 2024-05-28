#
# 
#

from collections.abc import Awaitable
import gettext
import logging

from bale import InlineKeyboardButton, InlineKeyboardMarkup, Message

from utils.types import (
    AbsPage, AbsWizard, CancelType, CbInput, DomainLang, BotVars, ID, TextInput, UserSpace,
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

    _CONFIRM_CBD = '10'

    _RESTART_CBD = '11'

    @classmethod
    def GetDescr(cls, bale_id: ID) -> str:
        global botVars
        return botVars.pDomains.GetStr(
            bale_id,
            'cmds_basic',
            'SIGNIN_CMD_DESCR')
    
    @property
    def Cancelable(self) -> CancelType:
        return CancelType.ASK

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
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    botVars.pDomains.GetStr(
                        self._baleId,
                        'cmds_basic',
                        'SIGN_IN_ENTER_FIRST_NAME')),
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
        firstInput = botVars.pUsers[self._baleId].GetFirstInput()
        if not isinstance(firstInput, TextInput):
            return self.LogReplyError(firstInput.bale_msg, True, 'E3-2')
        buttons = InlineKeyboardMarkup()
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        GetStr = botVars.pDomains.GetStr
        if self._firstName is None:
            self._firstName = firstInput.text
            buttons.add(self._GetRestartBtn())
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    GetStr(
                        self._baleId,
                        'cmds_basic',
                        'SIGN_IN_ENTER_LAST_NAME'),
                    components=buttons),
                False)
        elif self._lastName is None:
            self._lastName = firstInput.text
            buttons.add(self._GetRestartBtn())
            return WizardRes(
                self.Reply(
                    botVars.bot.send_message,
                    userSpace.GetFirstInput().bale_msg.chat_id,
                    GetStr(
                        self._baleId,
                        'cmds_basic',
                        'SIGN_IN_ENTER_PHONE'),
                    components=buttons),
                False)
        elif self._phone is None:
            # Saving data to 'phone'...
            self._phone = firstInput.text
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
        firstInput = userSpace.GetFirstInput()
        if not isinstance(firstInput, CbInput):
            return self.LogReplyError(firstInput.bale_msg, True, 'E3-3')
        match firstInput.cb:
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
                logging.error(f'{firstInput.cb}:')
                return WizardRes(None, False,)
    
    async def _Confirm(self) -> WizardRes:
        # Declaring variables -----------------------------
        global botVars
        gnuTrans: gettext.GNUTranslations
        userSpace: UserSpace
        # Asking for confirmation -------------------------
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        GetStr = botVars.pDomains.GetStr
        gnuTrans = botVars.pDomains.GetItem(
            DomainLang('cmds_basic', userSpace.dbUser.Lang))
        _ = gnuTrans.gettext
        pair = '{}: {}'
        text = GetStr(self._baleId, 'cmds_basic', 'ASK_CONFIRMATION')
        text += '\n' + pair.format(
            GetStr(self._baleId, 'cmds_basic', 'FIRST_NAME'),
            self._firstName)
        text += '\n' + pair.format(
            GetStr(self._baleId, 'cmds_basic', 'LAST_NAME'),
            self._lastName)
        text += '\n' + pair.format(
            GetStr(self._baleId, 'cmds_basic', 'PHONE'),
            self._phone)
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
        return InlineKeyboardButton(
            botVars.pDomains.GetStr(self._baleId, 'cmds', 'RESTART'),
            callback_data=f'{self.Uwid}-{self._RESTART_CBD}')

    def _GetConfirmBtn(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            botVars.pDomains.GetStr(self._baleId, 'cmds', 'CONFIRM'),
            callback_data=f'{self.Uwid}-{self._CONFIRM_CBD}')


class LangWiz(AbsWizard):
    CMD = '/lang'

    @classmethod
    def GetDescr(cls, bale_id: ID) -> str:
        return super().GetDescr(bale_id)

    def __init__(
            self,
            bale_id: ID,
            uw_id: str,
            cancel: CancelType = CancelType.ALLOWED,
            ) -> None:
        from typing import MutableMapping
        super().__init__(bale_id, uw_id)
        self._cancelType = cancel
        self._langStrs: MutableMapping[str, str] = {}
    
    @property
    def Cancelable(self) -> CancelType:
        return self._cancelType

    async def Start(self) -> WizardRes:
        global botVars
        return WizardRes(
            self.Reply(self._PrintLangs),
            False)
    
    async def ReplyText(self) -> WizardRes:
        # Declaring variables -----------------------------
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        firstInput = userSpace.GetFirstInput()
        GetStr = botVars.pDomains.GetStr
        # Replying ----------------------------------------
        if not isinstance(firstInput, TextInput):
            return self.LogReplyError(firstInput.bale_msg, True, 'E5-1')
        try:
            langCode = self._langStrs[firstInput.text.lower()]
            userSpace.dbUser.Lang = langCode
            return WizardRes(None, True)
        except KeyError:
            return WizardRes(self.GetLastReply(), False)
    
    async def ReplyCallback(self) -> WizardRes:
        # Declaring variables -----------------------------
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        firstInput = userSpace.GetFirstInput()
        GetStr = botVars.pDomains.GetStr
        # Replying ----------------------------------------
        if not isinstance(firstInput, CbInput):
            return self.LogReplyError(firstInput.bale_msg, True, 'E5-2')
        langCodes = set(self._langStrs.values())
        match firstInput.cb:
            case langCode if langCode in langCodes:
                userSpace.dbUser.Lang = langCode
                return WizardRes(None, True)
            case _:
                return self.LogReplyError(
                    firstInput.bale_msg,
                    True,
                    'E5-3',
                    firstInput.cb)

    async def _PrintLangs(self) -> Message:
        from . import IterLangs
        global botVars
        texts = list[str]()
        self._langStrs.clear()
        buttons = InlineKeyboardMarkup()
        for row, lang in enumerate(IterLangs(), 1):
            self._langStrs[lang.langCode.lower()] = lang.langCode
            self._langStrs[lang.langName.lower()] = lang.langCode
            texts.append(lang.selectMsg)
            buttons.add(
                InlineKeyboardButton(
                    text=lang.langName,
                    callback_data=f'{self.Uwid}-{lang.langCode}'),
                row)
        userSpace = botVars.pUsers.GetItemBypass(self._baleId)
        if texts:
            return botVars.bot.send_message(
                userSpace.GetFirstInput().bale_msg.chat_id, # type: ignore
                '\n'.join(texts),
                components=buttons)
        else:
            logging.error('E4-4', None, stack_info=True)
            return botVars.bot.send_message(
                bale_msg.chat_id, # type: ignore
                'An error occurred:\nE7',)
