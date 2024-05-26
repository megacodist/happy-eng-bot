#
# 
#
"""This module exposes the follwoings for this Bot:

#### Types

#### Dependencies
1. Python 3.12
2. `python-bale-bot`
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Awaitable
import enum
from functools import partial
import gettext
from pathlib import Path
from typing import TYPE_CHECKING, Callable
import logging

from bale import Bot, Message, User, InlineKeyboardButton, InlineKeyboardMarkup

from . import singleton
from db import ID, IDatabase, UserData


class UnsupportedLang(Exception):
    pass


class DomainNotFoundError(Exception):
    pass


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda x: x


class SDelHooks(enum.IntEnum):
    BEFORE_ACCESS = enum.auto()
    """This callback is invoked before member access. It accepts
    the hashable arguments of `SDelPool` API and returns `None`.
    """
    AFTER_ACCESS = enum.auto()
    """This callback is invoked after member access. The `KeyError`
    cancels this callback. It accepts the hashable arguments of
    `SDelPool` API and returns `None`.
    """
    ACCESS_KEY_ERROR = enum.auto()
    """This callback is invoked when `KeyError` occurred during memeber
    access. It accepts the hashable arguments of `SDelPool` API and
    returns `None`. It must find/load the object from a resource and put
    it in the pool usually by calling `SetItemBypass`. If callback can
    not find/load the object, it must raise a `KeyError`.
    """
    BEFORE_ASSIGNMENT = enum.auto()
    """This callback is invoked before member assignment. It accepts
    the hashable arguments of `SDelPool` API and returns `None`.
    """
    AFTER_ASSIGNMENT = enum.auto()
    """This callback is invoked after member assignment. The `KeyError`
    cancels this callback. It accepts the hashable arguments of
    `SDelPool` API and returns `None`.
    """
    BEFORE_DELETION = enum.auto()
    """This callback is invoked before member deletion. It accepts
    the hashable arguments of `SDelPool` API and returns `None`.
    """
    AFTER_DELETION = enum.auto()
    """This callback is invoked after member deletion. The `KeyError`
    cancels this callback. It accepts the hashable arguments of
    `SDelPool` API and returns `None`.
    """


class SDelPool[_Hashable, _SDelType]:
    """
    ### Deletion-scheduled pool of objects

    An object of this class is a pool of member objects accessible via
    keys. Memeber objects are scheduled for deletion after each access
    and get deleted after a specified amount of time if they do not access
    any more. This scheduling happens on `asyncio`.

    #### Methods:
    1. `GetItem`: gets an item with the key. There is also the sugar
    syntax of subscript operator (`a = sdelPool[key]`).
    2. `SetItem`: sets an item with the key and value. There is also
    the sugar syntax of subscript operator (`sdelPool[key[key] = a`).
    3. `DelItem`: deletes an item with the key. There is also the sugar
    syntax of subscript operator (`del sdelPool[key]`).

    #### Operators:
    1. `a = sdelPool[key]`
    2. `sdelPool[key[key] = a`
    3. `del sdelPool[key]`
    4. `key in sdelPool`
    """

    def __init__(
            self,
            *,
            auto: bool = True,
            del_timint: int = 3_600,
            ) -> None:
        """Initializes a new instance of this type. Arguments are as follow:

        * `auto`: `True` for automatic deletion scheduling, `False` for
        manual.
        * `del_timint`: the time interval after which any member object
        will be deleted if it has not accessed.
        """
        from asyncio import TimerHandle
        self._AUTO_DEL = auto
        """This boolan value specifies whether automatic deletion
        scheduling must be used or not.
        """
        self.DEL_TIMINT = del_timint
        """The time interval for deletion in seconds."""
        self._items: dict[_Hashable, _SDelType] = {}
        self._timers: dict[_Hashable, TimerHandle | None] = {}
        self._hooks: dict[SDelHooks, Callable[[_Hashable], None]] = {}
    
    def __getitem__(self, __key: _Hashable, /) -> _SDelType:
        return self.GetItem(__key)

    def __setitem__(self, __key: _Hashable, __value: _SDelType, /) -> None:
        self.SetItem(__key, __value)

    def __delitem__(self, __key: _Hashable, /) -> None:
        self.DelItem(__key)
    
    def __contains__(self, __key: _Hashable, /) -> bool:
        existed = __key in self._items
        if existed:
            self.ScheduleDel(__key)
        return existed
    
    def GetItemBypass(self, __key: _Hashable, /) -> _SDelType:
        """Gets the member object associated with the key bypassing
        deletion scheduling operations (scheduling, re-scheduling, or
        unscheduling). It raises `KeyError` if the key does not exist
        and may be suppressed if `ACCESS_KEY_ERROR` hook.
        """
        if SDelHooks.BEFORE_ACCESS in self._hooks:
            self._hooks[SDelHooks.BEFORE_ACCESS](__key)
        try:
            mem = self._items[__key]
        except KeyError as err:
            if SDelHooks.ACCESS_KEY_ERROR in self._hooks:
                self._hooks[SDelHooks.ACCESS_KEY_ERROR](__key)
                mem = self._items[__key]
            else:
                raise err
        else:
            if SDelHooks.AFTER_ACCESS in self._hooks:
                self._hooks[SDelHooks.AFTER_ACCESS](__key)
        return mem
    
    def SetItemBypass(self, __key: _Hashable, __value: _SDelType, /) -> None:
        """Sets the member object associated with the key bypassing
        deletion scheduling operations (scheduling, re-scheduling, or
        unscheduling). It raises `KeyError` if the key does not exist.
        """
        if SDelHooks.BEFORE_ASSIGNMENT in self._hooks:
            self._hooks[SDelHooks.BEFORE_ASSIGNMENT](__key)
        self._items[__key] = __value
        if SDelHooks.AFTER_ASSIGNMENT in self._hooks:
            self._hooks[SDelHooks.AFTER_ASSIGNMENT](__key)

    def _DelItemBypass(self, __key: _Hashable, /) -> None:
        """Deletes the specified key from internal data structures. It
        raises `KeyError` if the key does not exist. This API does not
        affect deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        import logging
        logging.debug(f'Deletion of {__key} key occurred in '
            f'{self.__class__.__qualname__}')
        if SDelHooks.BEFORE_DELETION in self._hooks:
            self._hooks[SDelHooks.BEFORE_DELETION](__key)
        del self._items[__key]
        del self._timers[__key]
        if SDelHooks.AFTER_DELETION in self._hooks:
            self._hooks[SDelHooks.AFTER_DELETION](__key)
    
    def GetItem(self, __key: _Hashable, /) -> _SDelType:
        """Gets the member object at the specified key and reset deletion
        scheduling. It raises `KeyError` if key does not exist. It is also
        possible to use sugar syntax of `a = sdelPool[key]`.
        """
        item = self.GetItemBypass(__key)
        self.ScheduleDel(__key)
        return item
    
    def SetItem(self, __key: _Hashable, __value: _SDelType, /) -> None:
        """Sets member object at the specified key and schedules it for
        deletion. It is also possible to use sugar syntax of
        `sdelPool[key] = a`.
        """
        self.SetItemBypass(__key, __value)
        self.ScheduleDel(__key)
    
    def DelItem(self, __key: _Hashable, /) -> None:
        """Deletes the specified member object with key. It raises
        `KeyError` if the key does not exist. It is possible to use
        the sugar syntax of `del sdelPool[key]` instead.
        """
        logging.debug(f'{self._items[__key]} is being deleted')
        if SDelHooks.BEFORE_DELETION in self._hooks:
            self._hooks[SDelHooks.BEFORE_DELETION](__key)
        self.UnscheduleDel(__key)
        del self._items[__key]
        del self._timers[__key]
        if SDelHooks.AFTER_DELETION in self._hooks:
            self._hooks[SDelHooks.AFTER_DELETION](__key)

    def ScheduleDel(
            self,
            key: _Hashable,
            del_timint: int | None = None,
            ) -> None:
        """Schedules a key for deletion. If it is already scheduled,
        it resets scheduling. It is also possible to specify a customize
        time interval, otherwise the default will be used.
        """
        import asyncio
        delTimInt = self.DEL_TIMINT if del_timint is None else del_timint
        self.UnscheduleDel(key)
        loop = asyncio.get_running_loop()
        self._timers[key] = loop.call_at(
            loop.time() + delTimInt,
            self._DelItemBypass,
            key)

    def UnscheduleDel(self, key: _Hashable) -> None:
        """Unschedules a key for deletion. If it has not scheduled, it
        has no eefect.
        """
        if (key in self._timers) and (self._timers[key] is not None):
            self._timers[key].cancel() # type: ignore
            if not self._timers[key].cancelled(): # type: ignore
                logging.fatal('E1-1', exc_info=True)
            self._timers[key] = None
    
    def Clear(self) -> None:
        keys = list(self._items.keys())
        for key in keys:
            self.DelItem(key)


class WizardRes:
    def __init__(
            self,
            reply: Awaitable[Message] | None,
            finished: bool,
            ) -> None:
        self.reply = reply
        self.finished = finished


class AbsPage(ABC):
    CMD: str
    """The literal of this command."""

    @classmethod
    @abstractmethod
    def GetDescr(cls, bale_id: ID) -> str:
        """Gets the description of the page."""
        pass

    @classmethod
    @abstractmethod
    async def Show(cls, bale_id: ID) -> None:
        pass


class CancelType(enum.IntEnum):
    ALLOWED = 1
    """The wizard can be canceled with no limitation."""
    ASK = 2
    """The wizard can be canceled but ask the user."""
    FORBIDDEN = 3
    """The wizard cannot be canceled."""


class AbsWizard(ABC):
    """Abstract base class for operations in the Bot. Implementations
    must avoid returning replies directly but rather use `Reply` method.
    Objects of this type supports the followings:

    1. hash protocol
    2. equality comparison
    """

    CMD: str
    """The literal of this command."""

    @classmethod
    @abstractmethod
    def GetDescr(cls, bale_id: ID) -> str:
        """Gets the description of the wizard."""
        pass
    
    def __init__(self, bale_id: ID, uw_id: str) -> None:
        self._baleId = bale_id
        """The ID of the user in the Bale."""
        self._UWID = uw_id
        """The unique ID of this wizard."""
        self._lastReply: partial[Awaitable[Message]] | None = None
        """The last reply of the operation."""
    
    def __hash__(self) -> int:
        return int(self._UWID)

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, self.__class__):
            return self._UWID == __obj._UWID
        return NotImplemented
    
    @property
    def Uwid(self) -> str:
        """Returns the unique ID of this operation."""
        return self._UWID
    
    @property
    @abstractmethod
    def Cancelable(self) -> CancelType:
        pass
    
    @property
    def LastReply(self) -> partial[Awaitable[Message]] | None:
        """Gets the last reply of the operation."""
        return self._lastReply
    
    def Reply(
            self,
            __coro: Callable[..., Awaitable[Message]] | None,
            /,
            *args,
            **kwargs,
            ) -> Awaitable[Message] | None:
        """Saves the last reply and returns it."""
        from functools import partial
        if __coro is None:
            self._lastReply = None
        else:
            self._lastReply = partial(__coro, *args, **kwargs)
        return self.GetLastReply()
    
    def GetLastReply(self) -> Awaitable[Message] | None:
        if self._lastReply is None:
            return None
        else:
            return self._lastReply()
    
    @abstractmethod
    async def Start(self)  -> WizardRes:
        """Starts this operation."""
        pass

    @abstractmethod
    async def ReplyText(self) -> WizardRes:
        """Optionally replies the provided text. It must return `True` if
        the operation finished otherwise `False`.
        """
        pass

    @abstractmethod
    async def ReplyCallback(self) -> WizardRes:
        """Optionally replies the provided callback. It must return `True`
        if the operation finished otherwise `False`. Callback data are in the
        format of `<uwid>-<cbnum>-<optional>`. The `Uwid` must be eliminated
        by operation manager and the rest must be fed into this method.
        """
        pass


class InputType(enum.IntEnum):
    """Specifies the types of input the end user can enter the Bot."""
    TEXT = 0
    CALLBACK = 1
    COMMAND = 2


class UserInput:
    def __init__(
            self,
            bale_msg: Message,
            type_: InputType,
            data: str,
            ) -> None:
        self.bale_msg = bale_msg
        self.type_ = type_
        self.data = data


class AbsInput(ABC):
    def __init__(
            self,
            bale_msg: Message,
            bale_id: ID,
            ) -> None:
        self.bale_msg = bale_msg
        self.bale_id = bale_id
    
    @abstractmethod
    async def Digest(self) -> None:
        pass


class TextInput(AbsInput):
    def __init__(
            self,
            bale_msg: Message,
            bale_id: ID,
            text: str,
            ) -> None:
        super().__init__(bale_msg, bale_id)
        self.text = text
        """The text that user typed into the Bot."""
    
    async def Digest(self) -> None:
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self.bale_id)
        if userSpace._wizard:
            res = await userSpace._wizard.ReplyText()
            if res.finished:
                userSpace._wizard = None
            if res.reply is not None:
                await userSpace.AppendOutput(res.reply)
        else:
            gnuTrans = botVars.pDomains.GetItem(
                DomainLang('cmds', userSpace.dbUser.Lang))
            _ = gnuTrans.gettext
            await userSpace.AppendOutput(self.bale_msg.reply(_('UNEX_DATA')))


class CbInput(AbsInput):
    def __init__(
            self,
            bale_msg: Message,
            bale_id: ID,
            cb_data: str,
            ) -> None:
        super().__init__(bale_msg, bale_id)
        parts = cb_data.split('-', 2)
        self.uwid = parts[0]
        self.cb = parts[1]
        self.extra = tuple(parts[2:])
    
    async def Digest(self) -> None:
        global botVars
        userSpace = botVars.pUsers.GetItemBypass(self.bale_id)
        if userSpace._wizard and (userSpace._wizard.Uwid == self.uwid):
            res = await userSpace._wizard.ReplyCallback()
            if res.finished:
                userSpace._wizard = None
            if res.reply is not None:
                await userSpace.AppendOutput(res.reply)
        else:
            gnuTrans = botVars.pDomains.GetItem(
                DomainLang('cmds', userSpace.dbUser.Lang))
            _ = gnuTrans.gettext
            await userSpace.AppendOutput(self.bale_msg.reply(_('EXPIRED_CB')))


class CmdInput(AbsInput):
    def __init__(
            self,
            bale_msg: Message,
            bale_id: ID,
            input_: str,
            ) -> None:
        super().__init__(bale_msg, bale_id)
        parts = input_.split()
        self.cmd = parts[0].lower()
        self.args = tuple(parts[1:])
    
    async def Digest(self) -> None:
        # DEclaring variables -----------------------------
        global botVars
        # Dispatching command -----------------------------
        try:
            pageType = botVars.pages[self.cmd]
            await pageType.Show(self.bale_id)
        except KeyError:
            userSpace = botVars.pUsers.GetItemBypass(self.bale_id)
            try:
                wizType = botVars.wizards[self.cmd]
                userSpace._wizard = wizType(
                    self.bale_id,
                    str(userSpace.dbUser.GetIncUwid()))
                res = await userSpace._wizard.Start()
                if res.finished:
                    userSpace._wizard = None
                if res.reply is not None:
                    await userSpace.AppendOutput(res.reply)
            except KeyError:
                gnuTrans = botVars.pDomains.GetItem(
                    DomainLang('cmds', userSpace.dbUser.Lang))
                _ = gnuTrans.gettext
                buttons = InlineKeyboardMarkup()
                buttons.add(InlineKeyboardButton(
                    _('HELP'),
                    callback_data='/help'))
                text = _('UNEX_CMD').format(self.cmd)
                await userSpace.AppendOutput(self.bale_msg.reply(
                    text,
                    components=buttons))


class _State(enum.IntEnum):
    SLEEP = enum.auto()
    PENDING = enum.auto()
    RUNNING = enum.auto()


class UserSpace:
    def __init__(self, db_user: UserData) -> None:
        self._inputs: deque[AbsInput] = deque()
        self._outputs: deque[Awaitable[Message]] = deque()
        self._digState = _State.SLEEP
        """The state of digestive algorithm."""
        self._repState = _State.SLEEP
        """The state of replying algorithm."""
        self.baleUser: User | None = None
        self.dbUser = db_user
        """The data of user in the database."""
        self._wizard: AbsWizard | None = None
        """The ongoing wizard."""
    
    def __repr__(self) -> str:
        return (f'<{self.__class__.__qualname__}'
            f' bale-id={self.baleUser.id}' # type: ignore
            f' bale-username={self.baleUser.username}>') # type: ignore
    
    async def ApendInput(self, input_: AbsInput) -> None:
        self._inputs.append(input_)
        if self._digState == _State.SLEEP:
            self._digState = _State.PENDING
            await self._Digest()

    async def AppendOutput(self, reply: Awaitable[Message]) -> None:
        self._outputs.append(reply)
        if self._repState == _State.SLEEP:
            self._repState = _State.PENDING
            await self._Reply()
    
    def CountInputs(self) -> int:
        """Returns number of inputs."""
        return len(self._inputs)
    
    def GetId(self) -> ID:
        return self.baleUser.id # type: ignore
    
    def GetFirstInput(self) -> AbsInput:
        """Gets first input from the queue without poping it. It raises
        `IndexError` if the queue is empty.
        """
        return self._inputs[0]
    
    def PopFirstInput(self) -> AbsInput:
        """Gets and removes first input from the queue. It raises
        `IndexError` if the queue is empty.
        """
        return self._inputs.popleft()
    
    def SuggestLS(self, bale_hour: int, percent: float) -> int:
        """Suggest the number of hours from `bale_hour` onwards that this
        `UserSpace` object has percent frequency greater than or equal to
        the specified percent frequency.
        """
        duration = 0
        while True:
            perFreq = self.dbUser.Frequencies.GetPercent(bale_hour)
            if perFreq >= percent and duration <= 24:
                bale_hour = 0 if bale_hour == 23 else (bale_hour + 1)
                duration += 1
            else:
                break
        return duration
    
    async def _Digest(self) -> None:
        self._digState = _State.RUNNING
        while self._inputs:
            await self.GetFirstInput().Digest()
            self.PopFirstInput()
        self._digState = _State.SLEEP
    
    async def _Reply(self) -> None:
        self._repState = _State.RUNNING
        while self._outputs:
            await self._outputs.popleft()
        self._repState = _State.SLEEP


class UserPool(SDelPool[ID, UserSpace]):
    def __init__(
            self,
            *,
            del_timint=3_600,
            ) -> None:
        super().__init__(del_timint=del_timint)
        self._hooks[SDelHooks.BEFORE_DELETION] = self._Save
        self._hooks[SDelHooks.ACCESS_KEY_ERROR] = self._Load
    
    def GetItemBypass(self, __key: ID) -> UserSpace:
        """Gets the `UserSpace` object associated with the key. If the
        object does not exist, it tries to load user data from database,
        If user information does not find in the database, it raises
        `KeyError`.
        """
        return super().GetItemBypass(__key)
    
    def _Load(self, key: ID) -> None:
        global botVars
        userData = botVars.db.GetUser(key)
        if userData is None:
            raise KeyError(f'User with ID={key} was neither found in {self}'
                ' nor database.')
        self.SetItemBypass(key, UserSpace(userData))
    
    def _Save(self, key: ID) -> None:
        global botVars
        botVars.db.UpsertUser(self.GetItemBypass(key).dbUser)
        logging.debug(f'{self._items[key]} saved to the database.')


class DomainLang:
    def __init__(self, domain: str, lang: str,) -> None:
        self.domain = domain
        self.lang = lang
    
    def __hash__(self) -> int:
        return hash(self.domain + self.lang)
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return NotImplemented
        return self.domain == value.domain and self.lang == value.lang
    
    def __repr__(self) -> str:
        return f"<{self.__qualname__} domain='{self.domain}' \
            lang=''{self.lang}>"


class DomainPool(SDelPool[DomainLang, gettext.GNUTranslations]):
    def __init__(
            self,
            *,
            auto: bool = True,
            del_timint: ID = 3_600,
            ) -> None:
        super().__init__(auto=auto, del_timint=del_timint)
        self._hooks[SDelHooks.ACCESS_KEY_ERROR] = self._Load
    
    def GetItem(self, __key: DomainLang) -> gettext.GNUTranslations:
        """Gets the `GNUTranslations` for the specified domain and
        language. It raises `KeyError` if it neither find it in the
        underlying data structure nor in the locales folder. In some
        rare cases it might raises `OSError`.
        """
        return super().GetItem(__key)
    
    def _Load(self, key: DomainLang,) -> None:
        """Loads the specified domain of the language and put in the
        underlying data structure. It raises `KeyError` if the domain
        of the languages does not exist. In some rare cases it might
        raises `OSError`.
        """
        global botVars
        try:
            gnuTrans = gettext.translation(
                domain=key.domain,
                localedir=botVars.LOCALES_DIR,
                languages=[key.lang,])
        except FileNotFoundError:
            raise KeyError()
        else:
            self.SetItemBypass(key, gnuTrans)
    
    def GetStr(self, bale_id: ID, domain: str, msg_id: str) -> str:
        """Gets the string associated with `msg_id` from the specified
        domain in the language selected by Bale user.

        #### Exceptions:
        * `UnsupportedLang`
        * `DomainNotFoundError`
        """
        # Declaring variables -----------------------------
        global botVars
        userSpace: UserSpace
        lang: str
        # Getting string ----------------------------------
        userSpace = botVars.pUsers.GetItemBypass(bale_id)
        lang = userSpace.dbUser.Lang
        if lang not in botVars.langs:
            raise UnsupportedLang()
        try:
            gnuTrans = self.GetItem(DomainLang(domain, lang))
        except FileNotFoundError:
            langDir = botVars.BOT_DIR / botVars.LOCALES_DIR / lang / \
                'LC_MESSAGES'
            if not langDir.exists():
                raise UnsupportedLang()
            logging.error('E4-1', bale_id, domain, lang, stack_info=True)
            # Getting the string of the default language...
            lang = botVars.defaultLang
            try:
                gnuTrans = self.GetItem(DomainLang(domain, lang))
            except KeyError:
                logging.error('E4-1', bale_id, domain, lang, stack_info=True)
                raise DomainNotFoundError()
        msgStr = gnuTrans.gettext(msg_id)
        if msgStr == msg_id:
            logging.error(
                'E4-2',
                bale_id,
                msg_id,
                domain,
                lang,
                stack_info=True)
        return msgStr


class BotVars(object, metaclass=singleton.SingletonMeta):
    ADMIN_IDS: tuple[int, ...] = tuple()
    """A tuple of ID's of admin users."""

    BOT_DIR: Path
    """The directory of the Bot."""

    bot: Bot

    db: IDatabase
    """The database of the Bot."""

    MIN_USER_LS: int = 3_600
    """The minimum life span of `UserSpace` objects in seconds."""

    PERCENT_LIFE = 0.05
    """"""

    pUsers: UserPool
    """A mapping of `ID -> UserData` contains all information of recent users
    of the Bot.
    """

    pages: dict[str, type[AbsPage]] = {}

    wizards: dict[str, type[AbsWizard]] = {}

    LOCALES_DIR: str
    """The directory of the translated strings in the format of GNU
    gettext API.
    """

    pDomains: DomainPool
    """A mapping of `DomainLang -> GNUTranslations` contains all
    translation objects for all domains and all supported languages of
    the Bot.
    """

    defaultLang: str
    """The default language of the Bot."""

    def __init__(self) -> None:
        self.pUsers = UserPool(del_timint=self.MIN_USER_LS)
        self.pDomains = DomainPool(del_timint=self.MIN_USER_LS)
        self._langs: tuple[str, ...]
    
    @property
    def langs(self) -> tuple[str, ...]:
        """Gets a tuple of all supported languages."""
        try:
            return self._langs
        except AttributeError:
            return self.GetLangs()
    
    def GetLangs(self) -> tuple[str, ...]:
        """Scans for all installed languages, saves them to `langs` property
         and returns them as a tuple.
         """
        langs = []
        localesDir = self.BOT_DIR / self.LOCALES_DIR
        if localesDir.is_dir():
            for entry in localesDir.iterdir():
                lang_dir = entry / 'LC_MESSAGES'
                if lang_dir.is_dir():
                    mo_files = list(lang_dir.glob('*.mo'))
                    if mo_files:
                        langs.append(entry.name)
        self._langs = tuple(langs)
        return self._langs


botVars = BotVars()
