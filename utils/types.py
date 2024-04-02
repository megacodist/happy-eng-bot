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
import enum
from typing import Any, Callable, TypeVar
import logging
from typing import Any, Coroutine, TypeVar

from bale import (
    Bot, Message, User, InlineKeyboardButton, InlineKeyboardMarkup)

from db import ID, IDatabase, UserData
import lang


class HappyEngBot(Bot):
    def __init__(
            self,
            token: str,
            db: IDatabase,
            user_pool: UserPool,
            op_pool: OperationPool,
            **kwargs,
            ) -> None:
        super().__init__(token, **kwargs)
        self.db = db
        self.user_pool = user_pool
        self.op_pool = op_pool


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
        return self._items[__key]
    
    def SetItemBypass(self, __key: _Hashable, __value: _SDelType, /) -> None:
        """Sets the member object associated with the key bypassing
        deletion scheduling operations (scheduling, re-scheduling, or
        unscheduling). It raises `KeyError` if the key does not exist.
        """
        self._items[__key] = __value

    def DeleteItemBypass(self, __key: _Hashable, /) -> None:
        """Deletes the specified key from internal data structures. It
        raises `KeyError` if the key does not exist. This API does not
        affect deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        import logging
        logging.debug(f'Deletion of {__key} key occurred in '
            f'{self.__class__.__qualname__}')
        del self._items[__key]
        del self._timers[__key]
    
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


class UserPool(LSDelPool[ID, UserData]):
    def __init__(
            self,
            db: IDatabase,
            *,
            del_timint=20,
            ) -> None:
        super().__init__(db, del_timint=del_timint)
    
    def Load(self, key: int) -> UserData:
        userData = self._db.GetUser(key)
        if userData is None:
            raise KeyError()
        logging.debug(f'The user with {key} has been loaded into '
            f'{self.__class__.__qualname__}')
        return userData
    
    def Save(self, key: ID) -> None:
        self._db.UpsertUser(self._items[key])
        logging.debug(f'{self._items[key]} saved to the database.')


class AbsOperation(ABC):
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
    
    def __init__(
            self,
            user_data: UserData | None = None
            ) -> None:
        """Initializes a new operation which can be optionally associated
        with a user.
        """
        self._UID = AbsOperation.GenerateUid()
        """The unique ID of this operation."""
        self._userData = user_data
        """The optional user data associated with this operation."""
        self._lastReply: Coroutine[Any, Any, Message] | None = None
        """The last reply of the operation."""
    
    def __hash__(self) -> int:
        return self._UID

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, AbsOperation):
            return self._UID == __obj._UID
        return NotImplemented
    
    @property
    def Uid(self) -> int:
        """Returns the unique ID of this operation."""
        return self._UID
    
    @property
    def UserData(self) -> UserData | None:
        """Gets the optional user data associated with this operation."""
        return self._userData
    
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
    def Start(
            self,
            message: Message
            )  -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        """Starts this operation."""
        pass

    @abstractmethod
    def ReplyText(
            self,
            message: Message,
            text: str,
            ) -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        """Optionally replies the provided text. It must return `True` if
        the operation finished otherwise `False`.
        """
        pass

    def ReplyCallback(
            self,
            message: Message,
            cb: str,
            ) -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        """Optionally replies the provided callback. It must return `True`
        if the operation finished otherwise `False`. Callback data are in the
        format of `<uid>-<cbnum>-<optional>`. The `Uid` must be eliminated
        by operation manager and the rest must be fed into this method.
        """
        pass


class SigninOp(AbsOperation):
    """Encapsulates a sign-in operation in the Bot. You should start
    this operation by calling `Start` method.
    """

    CONFIRM_CBD = '10'

    RESTART_CBD = '11'

    def __init__(
            self,
            bale_id: ID,
            user_pool: UserPool,
            ) -> None:
        """Initializes a new instance of the sign-in operation with the
        Bale ID of the user.
        """
        super().__init__()
        self._baleId = bale_id
        """The Bale ID of the user."""
        self._userPool = user_pool
        self._firstName: str | None = None
        self._lastName: str | None = None
        self._phone: str | None = None

    def Start(
            self,
            message: Message
            ) -> Coroutine[Any, Any, Message]:
        return self.Reply(message.reply, lang.SIGN_IN_ENTER_FIRST_NAME)

    def ReplyText(
            self,
            message: Message,
            text: str,
            ) -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        """Gets from user and fills folowing items in consecutive calls:
        1. first name
        2. last name
        3. e-mail
        4. phone no.
        """
        buttons = InlineKeyboardMarkup()
        if self._firstName is None:
            self._firstName = text
            self._AppendRestartBtn(buttons)
            return (
                self.Reply(
                    message.reply,
                    lang.SIGN_IN_ENTER_LAST_NAME,
                    components=buttons),
                False)
        elif self._lastName is None:
            self._lastName = text
            self._AppendRestartBtn(buttons)
            return (
                self.Reply(
                    message.reply,
                    lang.SIGN_IN_ENTER_PHONE,
                    components=buttons),
                False)
        elif self._phone is None:
            # Saving data to 'phone'...
            self._phone = text
            # Confirming all data...
            buttons.add(InlineKeyboardButton(
                lang.CONFIRM,
                callback_data=f'{self.CONFIRM_CBD}'))
            buttons.add(InlineKeyboardButton(
                lang.RESTART,
                callback_data=f'{self.RESTART_CBD}'))
            response = '{0}\n{1}: {2}\n{3}: {4}\n{5}: {6}'.format(
                lang.CONFIRM_DATA,
                lang.FIRST_NAME,
                self._firstName,
                lang.LAST_NAME,
                self._lastName,
                lang.PHONE,
                self._phone)
            return (
                self.Reply(message.reply, response, components=buttons),
                False,)
        else:
            logging.error('E1-3')
            return (None, False,)

    def ReplyCallback(
            self,
            bale_msg: Message,
            cb_data: str,
            ) -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        match cb_data:
            case self.CONFIRM_CBD:
                self._userPool[self._baleId] = UserData(
                    self._baleId,
                    self._firstName,
                    self._lastName,
                    self._phone)
                return (self.Reply(None), True,)
            case self.RESTART_CBD:
                self._firstName = None
                self._lastName = None
                self._phone = None
                return (self.Reply(self.Start, bale_msg), False,)
            case _:
                logging.error(f'{cb_data}: unknown callback in '
                    f'{self.__class__.__qualname__}')
                return (None, False,)
    
    def _AppendRestartBtn(self, buttons: InlineKeyboardMarkup) -> None:
        buttons.add(InlineKeyboardButton(
        lang.RESTART,
        callback_data=f'{self.RESTART_CBD}'))


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
