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
import enum
from typing import Any, Callable, TypeVar
import logging
from typing import Any, Coroutine, TypeVar

from bale import Message, User

from db import ID, IDatabase, UserData
import lang


# Bot-wide variables ================================================
pages: dict[str, PgCallback]

wizards: dict[str, AbsWizard]


def InitModule(
        *,
        pages_: dict[str, PgCallback],
        wizards_: dict[str, AbsWizard],
        **kwargs,
        ) -> None:
    # Declaring variables ---------------------------------
    global pages
    global wizards
    # Functoning ------------------------------------------
    pages = pages_
    wizards = wizards_


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
    access. It accepts the hashable arguments of `SDelPool` API and the
    `KeyError` object and returns `None`. If callback can not resolve
    the problem, it must re-raise the exception.
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


_Hashable = TypeVar('_Hashable')

_SDelType = TypeVar('_SDelType')

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
            del_timint=3_600,
            ) -> None:
        """Initializes a new instance of this type. Arguments are as follow:

        * `del_timint`: the time interval after which any member object
        will be deleted if it has not accessed.
        """
        from asyncio import TimerHandle
        from collections import defaultdict
        self._DEL_TIMINT = del_timint
        """The time interval for deletion in seconds."""
        self._items: dict[_Hashable, _SDelType] = {}
        self._timers: dict[_Hashable, TimerHandle] = {}
        self._hooks: dict[SDelHooks, Callable[[_Hashable], None]] = {}
    
    def __getitem__(self, __key: _Hashable, /) -> _SDelType:
        return self.GetItem(__key)

    def __setitem__(self, __key: _Hashable, __value: _SDelType, /) -> None:
        self.SetItem(__key, __value)

    def __delitem__(self, __key: _Hashable, /) -> None:
        self.DelItem(__key)
    
    def __contains__(self, __key: _Hashable, /) -> None:
        existed = __key in self._items
        if existed:
            self.ScheduleDel(__key)
        return existed
    
    def GetItemBypass(self, __key: _Hashable, /) -> _SDelType:
        """Gets the member object associated with the key bypassing
        deletion scheduling operations (scheduling, re-scheduling, or
        unscheduling). It raises `KeyError` if the key does not exist.
        """
        if SDelHooks.BEFORE_ACCESS in self._hooks:
            self._hooks[SDelHooks.BEFORE_ACCESS](__key)
        try:
            mem = self._items[__key]
        except KeyError as err:
            if SDelHooks.ACCESS_KEY_ERROR in self._hooks:
                mem = self._hooks[SDelHooks.ACCESS_KEY_ERROR](__key, err)
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

    def DelItemBypass(self, __key: _Hashable, /) -> None:
        """Deletes the specified key from internal data structures. It
        raises `KeyError` if the key does not exist. This API does not
        affect deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        import logging
        logging.debug(f'Deletion of {__key} key occurred in '
            f'{self.__class__.__qualname__}')
        if SDelHooks.BEFORE_DELETION in self._hooks:
            self._hooks[SDelHooks.BEFORE_ASSIGNMENT](__key)
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
        del self._items[__key]
        self.UnscheduleDel(__key)
        del self._timers[__key]

    def ScheduleDel(self, key: _Hashable) -> None:
        """Schedules a key for deletion. If it is already scheduled,
        it resets scheduling.
        """
        import asyncio
        self.UnscheduleDel(key)
        loop = asyncio.get_running_loop()
        self._timers[key] = loop.call_at(
            loop.time() + self._DEL_TIMINT,
            self.DelItemBypass,
            key)

    def UnscheduleDel(self, key: _Hashable) -> None:
        """Unschedules a key for deletion. If it has not scheduled, it
        has no eefect.
        """
        if key in self._timers:
            self._timers[key].cancel()
            if not self._timers[key].cancelled():
                logging.fatal('E1-1', exc_info=True)
            self._timers[key] = None
    
    def Clear(self) -> None:
        for key in self._items:
            self.UnscheduleDel(key)
            self.DelItemBypass(key)


type PgCallback = Callable[[ID], Coroutine[Any, Any, Message]]
"""The signature for any callable object to be qualified as a `Page`."""


class Page:
    def __init__(
            self,
            cmd: str,
            callback: PgCallback,
            ) -> None:
        self.cmd = cmd
        self.callback = callback


class WizardRes:
    def __init__(
            self,
            reply: Coroutine[Any, Any, Message] | None,
            finished: bool,
            ) -> None:
        self.reply = reply
        self.finished = finished


class AbsWizard(ABC):
    """Abstract base class for operations in the Bot. Implementations
    must avoid returning replies directly but rather use `Reply` method.
    Objects of this type supports the followings:

    1. hash protocol
    2. equality comparison
    """
    _nId = 1
    """This attribute is used to produce unique id in `GenerateUid` class
    method.
    """

    CMD: str
    """The literal of this command."""

    @classmethod
    def GenerateUid(cls) -> int:
        """Generates a unique id. This uniqueness is guaranteed among
        all instances of this class even deleted ones.
        """
        uid = cls._nId
        cls._nId += 1
        if cls._nId > 0xff_ff_ff_ff:
            cls._nId = 1
        return uid
    
    def __init__(self, bale_id: ID) -> None:
        self._UID = self.GenerateUid()
        """The unique ID of this operation."""
        self._baleId = bale_id
        """The ID of the user in the Bale."""
        self._lastReply: Coroutine[Any, Any, Message] | None = None
        """The last reply of the operation."""
    
    def __hash__(self) -> int:
        return self._UID

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, self.__class__):
            return self._UID == __obj._UID
        return NotImplemented
    
    @property
    def Uid(self) -> int:
        """Returns the unique ID of this operation."""
        return self._UID
    
    @property
    def LastReply(self) -> Coroutine[Any, Any, Message] | None:
        """Gets the last reply of the operation."""
        return self._lastReply
    
    def Reply(
            self,
            __coro: Coroutine[Any, Any, Message] | None,
            /,
            *args,
            **kwargs,
            ) -> Coroutine[Any, Any, Message] | None:
        """Saves the last reply and returns it."""
        from functools import partial
        if __coro is None:
            self._lastReply = None
        else:
            self._lastReply = partial(__coro, *args, **kwargs)
        return self.GetLastReply()
    
    def GetLastReply(self) -> Coroutine[Any, Any, Message] | None:
        if self._lastReply is None:
            return None
        else:
            return self._lastReply()
    
    @abstractmethod
    def Start(self)  -> WizardRes:
        """Starts this operation."""
        pass

    @abstractmethod
    def ReplyText(self) -> WizardRes:
        """Optionally replies the provided text. It must return `True` if
        the operation finished otherwise `False`.
        """
        pass

    def ReplyCallback(self) -> WizardRes:
        """Optionally replies the provided callback. It must return `True`
        if the operation finished otherwise `False`. Callback data are in the
        format of `<uid>-<cbnum>-<optional>`. The `Uid` must be eliminated
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


class UserSpace:
    def __init__(self) -> None:
        self._inputs: deque[UserInput] = deque()
        self._baleUser: User | None = None
        self._dbUser: UserData
        self._wizard: AbsWizard | None = None
    
    def ApendInput(self, ui: UserInput) -> None:
        self._inputs.append(ui)
    
    def CountInputs(self) -> int:
        """Returns number of inputs."""
        return len(self._inputs)
    
    def GetId(self) -> ID:
        return self._baleUser.id
    
    def GetFirstInput(self) -> UserInput:
        """Gets first input from the queue without poping it. It raises
        `IndexError` if the queue is empty.
        """
        return self._inputs[0]
    
    def PopFirstInput(self) -> UserInput:
        """Gets and removes first input from the queue. It raises
        `IndexError` if the queue is empty.
        """
        return self._inputs.popleft()
    
    def ReplyNextInput(self) -> Coroutine[Any, Any, Message] | None:
        """Gets the reply for the next input. It does nothing if there is
        no input.
        """
        try:
            input_ = self.GetFirstInput()
        except IndexError:
            return
        match input_.type_:
            case InputType.TEXT:
                return self._GetTextReply()
            case InputType.CALLBACK:
                return self._GetCbReply()
            case InputType.COMMAND:
                return self._GetCmdReply()
    
    def _GetTextReply(self) -> Coroutine[Any, Any, Message] | None:
        if self._wizard:
            res = self._wizard.ReplyText()
            self.PopFirstInput()
            if res.finished:
                self._wizard = None
            return res.reply
        else:
            return  self.GetFirstInput().bale_msg.reply(lang.UNEX_DATA)
    
    def _GetCbReply(self) -> Coroutine[Any, Any, Message] | None:
        if self._wizard:
            res = self._wizard.ReplyCallback()
            self.PopFirstInput()
            if res.finished:
                self._wizard = None
            return res.reply
        else:
            return self.GetFirstInput().bale_msg.reply(lang.EXPIRED_CB)
    
    def _GetCmdReply(self) -> Coroutine[Any, Any, Message] | None:
        # DEclaring variables -----------------------------
        global pages
        global wizards
        # Dispatching command -----------------------------
        try:
            return pages[self.GetFirstInput().data](self.GetId())
        except KeyError:
            try:
                wiz = wizards[self.GetFirstInput().data](self.GetId())
            except KeyError:
                return pages['/help'](self._baleUser.id)


class UserPool(SDelPool[ID, UserSpace]):
    def __init__(
            self,
            db: IDatabase,
            *,
            del_timint=20,
            ) -> None:
        super().__init__(del_timint=del_timint)
        self._db = db
        self._hooks[SDelHooks.BEFORE_DELETION] = self._Save
        self._hooks[SDelHooks.ACCESS_KEY_ERROR] = self._Load
    
    def _Load(self, key: int, err: KeyError) -> UserData:
        userData = self._db.GetUser(key)
        if userData is None:
            raise err
        else:
            self._items[key] = userData
        logging.debug(f'The user with {key} has been loaded into '
            f'{self.__class__.__qualname__}')
        return userData
    
    def _Save(self, key: ID) -> None:
        self._db.UpsertUser(self._items[key])
        logging.debug(f'{self._items[key]} saved to the database.')
    
    def Close(self) -> None:
        super().Clear()
