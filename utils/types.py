#
# 
#
"""This module exposes the follwoings for this Bot:

#### Types
1. `Commands`

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

from bale import (
    Bot, Message, User, InlineKeyboardButton, InlineKeyboardMarkup)

from cmds import AbsWizard
from db import ID, IDatabase, UserData
import lang


class Commands(enum.Enum):
    """This enumeration contains all the supported commands of this Bot.
    The value of each enumerator is its shell command.
    """
    ADMIN = '/admin'
    HELP = '/help'
    MY_COURSES = '/mycourses'
    SIGN_IN = '/signin'
    SHOWCASE = '/showcase'
    START = '/start'


class InputType(enum.IntEnum):
    """Specifies the types of input the end user can enter the Bot."""
    TEXT = 0
    CALLBACK = 1
    COMMAND = 2


class SDelHooks(enum.IntEnum):
    BEFORE_ACCESS = enum.auto()
    """These callables are invoked before member access. They accept
    the hashable arguments of `SDelPool` API and return `None`.
    """
    AFTER_ACCESS = enum.auto()
    """These callables are invoked after member access. The `KeyError`
    cancels these callables. They accept the hashable arguments of
    `SDelPool` API and return `None`.
    """
    ACCESS_KEY_ERROR = enum.auto()
    """These callables are invoked when `KeyError` occurred during memeber
    access. They must accept the hashable arguments of `SDelPool` API and
    return a boolean value. `True` to suppress `KeyError` or `False` to
    re-raise it. If there is at least one `True`, the error will be
    canceled.
    """
    BEFORE_ASSIGNMENT = enum.auto()
    """These callables are invoked before member assignment. They accept
    the hashable arguments of `SDelPool` API and return `None`.
    """
    AFTER_ASSIGNMENT = enum.auto()
    """These callables are invoked after member assignment. They accept
    the hashable arguments of `SDelPool` API and return `None`.
    """
    BEFORE_DELETION = enum.auto()
    """These callables are invoked before member deletion. They accept
    the hashable arguments of `SDelPool` API and return `None`.
    """
    AFTER_DELETION = enum.auto()
    """These callables are invoked after member deletion. They accept
    the hashable arguments of `SDelPool` API and return `None`.
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
        self._DEL_TIMINT = del_timint
        """The time interval for deletion in seconds."""
        self._items: dict[_Hashable, _SDelType] = {}
        self._timers: dict[_Hashable, TimerHandle] = {}
        self._hooks: dict[SDelHooks, list[Callable[[_Hashable], None]]] = {}
    
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
        #return self._items[__key]
        for cb in self._hooks[SDelHooks.BEFORE_ACCESS]:
            cb(__key)
        try:
            mem = self._items[__key]
            for cb in self._hooks[SDelHooks.AFTER_ACCESS]:
                cb(__key)
        except KeyError as err:
            suppression = False
            for cb in self._hooks[SDelHooks.ACCESS_KEY_ERROR]:
                suppression |= cb(__key)
            if not suppression:
                raise err
    
    def SetItemBypass(self, __key: _Hashable, __value: _SDelType, /) -> None:
        """Sets the member object associated with the key bypassing
        deletion scheduling operations (scheduling, re-scheduling, or
        unscheduling). It raises `KeyError` if the key does not exist.
        """
        for cb in self._hooks[SDelHooks.BEFORE_ASSIGNMENT]:
            cb(__key)
        self._items[__key] = __value
        for cb in self._hooks[SDelHooks.AFTER_ASSIGNMENT]:
            cb(__key)

    def DeleteItemBypass(self, __key: _Hashable, /) -> None:
        """Deletes the specified key from internal data structures. It
        raises `KeyError` if the key does not exist. This API does not
        affect deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        import logging
        logging.debug(f'Deletion of {__key} key occurred in '
            f'{self.__class__.__qualname__}')
        for cb in self._hooks[SDelHooks.BEFORE_DELETION]:
            cb(__key)
        del self._items[__key]
        del self._timers[__key]
        for cb in self._hooks[SDelHooks.AFTER_DELETION]:
            cb(__key)
    
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
            self.DeleteItemBypass,
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


class LSDelPool(ABC, SDelPool[_Hashable, _SDelType]):
    """
    #### Load-save SDelPool
    Objects of this type act like `SDelPool` but upon failure in
    access, it tries to load the object via `Load` method; and before
    deletion it saves the member object via `Save` method.
    """
    def __init__(
            self,
            db: IDatabase,
            *,
            del_timint=3_600,
            ) -> None:
        super().__init__(del_timint=del_timint)
        self._db = db
        """The database object"""
    
    @abstractmethod
    def Load(self, key: _Hashable) -> _SDelType:
        """Loads member object when the key is not available. If it cannot
        load the member object, it must raise `KeyError` exception.
        """
        pass

    @abstractmethod
    def Save(self, key: _Hashable) -> None:
        """Saves the member object just before deletion. If it cannot
        load the member object, it must throws `KeyError` exception.
        """
        pass

    def __contains__(self, __key: _Hashable) -> None:
        existed = super().__contains__(__key)
        if existed:
            return True
        try:
            item = self.Load(__key)
            self.SetItem(__key, item)
            return True
        except KeyError:
            return False

    def GetItemBypass(self, __key: _Hashable, /) -> _SDelType:
        try:
            item = super().GetItemBypass(__key)
        except KeyError:
            item = self.Load(__key)
            self.SetItem(__key, item)
        return item

    def DeleteItemBypass(self, __key: _Hashable, /) -> None:
        self.Save(__key)
        super().DeleteItemBypass(__key)
    
    def close(self) -> None:
        for key in self._items:
            self.Save(key)
        self._items.clear()


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
        self._baleUser = None
        self._dbUser: UserData
        self._wizard: AbsWizard | None = None
    
    def ApendInput(self, ui: UserInput) -> None:
        self._inputs.append(ui)
    
    def CountInputs(self) -> int:
        """Returns number of inputs."""
        return len(self._inputs)
    
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
        pass


class UserPool(SDelPool[ID, UserSpace]):
    def __init__(
            self,
            db: IDatabase,
            *,
            del_timint=20,
            ) -> None:
        super().__init__(db, del_timint=del_timint)
        self._db = db
        self._hooks[SDelHooks.BEFORE_DELETION].append(self._Save)
        self._hooks[SDelHooks.ACCESS_KEY_ERROR].append(self._Load)
    
    def _Load(self, key: int) -> UserData:
        userData = self._db.GetUser(key)
        if userData is None:
            raise KeyError()
        logging.debug(f'The user with {key} has been loaded into '
            f'{self.__class__.__qualname__}')
        return userData
    
    def _Save(self, key: ID) -> None:
        self._db.UpsertUser(self._items[key])
        logging.debug(f'{self._items[key]} saved to the database.')





class OperationPool(SDelPool[ID, AbsOperation]):

    CANCELED_BY_CMD_CBD = '1'
    """The infix of the callback data denotes cancelation of this
    operation by a command. The callback data must have this format:
    `<uid>-1-/<cmd>`
    """

    CONTINUE_CBD = '2'
    """The suffix of the callback data which denotes that this operation
    to be continued. The callback data must have this format:
    `<uid>-2`
    """

    def __init__(
            self,
            user_pool: UserPool,
            cmd_dispatcher: Callable[[Message, User, str],
                Coroutine[Any, Any, Message]],
            ) -> None:
        super().__init__()
        self._ops: dict[UserData, AbsOperation] = {}
        """The mapping of all the ongoing operations."""
        self._cmdDispatcher = cmd_dispatcher
        self._userPool = user_pool
        """The user pool of the Bot."""
        self._UID = 0
        """The unique ID of the operation pool. All operations' UID are
        positive (as a result larger than 0).
        """

    def GetTextReply(
            self,
            bale_msg: Message,
            bale_user: User,
            text: str,
            ) -> Coroutine[Any, Any, Message] | None:
        """Gets the optional reply of the user provided text. It raises
        `KeyError` if the user does not have an ongoing operation.
        """
        # Re-scheduling the user...
        try:
            self._userPool[bale_user.id]
        except KeyError:
            pass
        # Getting the reply...
        reply, finished = self[bale_user.id].ReplyText(bale_msg, text)
        if finished:
            self.DelItem(bale_user.id)
        return reply

    def GetCallbackReply(
            self,
            bale_msg: Message,
            bale_user: User,
            cb_data: str,
            ) -> Coroutine[Any, Any, Message] | None:
        """Gets the optional reply of the callback. It raises
        `KeyError` if the user does not have an ongoing operation.
        """
        # Re-scheduling the user...
        try:
            self._userPool[bale_user.id]
        except KeyError:
            pass
        self.GetItem(bale_user.id)
        # Getting the reply...
        from .funcs import SplitOnDash
        cmd = None
        parts = SplitOnDash(cb_data)
        if parts[0] != str(self._UID):
            reply, finished = self._items[bale_user.id].ReplyCallback(
                bale_msg,
                cb_data)
        else:
            match parts[1].split('-'):
                case [self.CANCELED_BY_CMD_CBD, cmd,]:
                    finished = True
                case [self.CONTINUE_CBD,]:
                    reply = self[bale_user.id].GetLastReply()
                    finished = False
                case _:
                    logging.error(f'{cb_data}: unknown callback in '
                        f'{self.__class__.__qualname__}')
                    reply = None
                    finished = False
        if finished:
            self.DelItem(bale_user.id)
        if cmd is None:
            return reply
        else:
            return self._cmdDispatcher(bale_msg, bale_user, cmd)

    def CancelByCmdReply(
            self,
            bale_msg: Message,
            bale_user: User,
            cmd: str,
            ) -> Coroutine[Any, Any, Message]:
        """Gets a reply informing user of canceling the ongoing operation
        to pursue the passed-in command. It raises `KeyError` if the user
        does not have an ongoing operation.
        """
        # Re-scheduling the user...
        try:
            self._userPool[bale_user.id]
        except KeyError:
            pass
        # Checking if the user has an ongoing operation...
        self.GetItem(bale_user.id)
        # Asking for cancelation...
        buttons = InlineKeyboardMarkup()
        buttons.add(InlineKeyboardButton(
            lang.CONTINUE_OP,
            callback_data=f'{self._UID}-{self.CONTINUE_CBD}'))
        buttons.add(InlineKeyboardButton(
            lang.CANCEL_OP,
            callback_data=f'{self._UID}-{self.CANCELED_BY_CMD_CBD}-{cmd}'))
        return bale_msg.reply(lang.DISRUPTIVE_CMD, components=buttons)
