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

from abc import ABC, abstractmethod
from asyncio import sleep, TimerHandle
import enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
import logging
from typing import Any, Callable, Coroutine, TypeVar

from bale import Message, User, InlineKeyboardButton, InlineKeyboardMarkup

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


_SDelType = TypeVar('_SDelType')


class SDelPool[_SDelType]:
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

    def __init__(self) -> None:
        """Initializes a new instance of this type."""

        from asyncio import TimerHandle
        self._DEL_TIMINT = 3_600
        """The time interval for deletion in seconds."""
        self._items: dict[ID, _SDelType] = {}
        self._timers: dict[ID, TimerHandle] = {}
    
    def __getitem__(self, __key: ID, /) -> _SDelType:
        return self.GetItem(__key)

    def __setitem__(self, __key: ID, __value: _SDelType, /) -> None:
        self.SetItem(__key, __value)

    def __delitem__(self, __key: ID, /) -> None:
        self.DelItem(__key)
    
    def __contains__(self, __key: ID, /) -> None:
        return __key in self._items
    
    def _GetKey(self, __key: ID, /) -> _SDelType:
        """Gets the member object associated with the key. It raises
        `KeyError` if the key does not exist. This API does not affect
        deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        return self._items[__key]
    
    def _SetKey(self, __key: ID, __value: _SDelType, /) -> None:
        """Sets the member object associated with the key. This API does
        not affect deletion scheduling in any way (scheduling, re-scheduling,
        or unscheduling).
        """
        self._items[__key] = __value

    def _DeleteKey(self, __key: ID, /) -> None:
        """Removes the specified key from internal data structures. It
        raises `KeyError` if the key does not exist. This API does not
        affect deletion scheduling in any way (scheduling, re-scheduling, or
        unscheduling).
        """
        del self._items[__key]
        del self._timers[__key]
    
    def GetItem(self, __key: ID, /) -> _SDelType:
        """Gets the member object at the specified key and reset deletion
        scheduling. It raises `KeyError` if key does not exist. It is also
        possible to use sugar syntax of `a = sdelPool[key]`.
        """
        item = self._GetKey(__key)
        self.ScheduleDel(__key)
        return item
    
    def SetItem(self, __key: ID, __value: _SDelType, /) -> None:
        """Sets member object at the specified key and schedules it for
        deletion. It is also possible to use sugar syntax of
        `sdelPool[key] = a`.
        """
        self._SetKey(__key, __value)
        self.ScheduleDel(__key)
    
    def DelItem(self, __key: ID, /) -> None:
        """Deletes the specified member object with key. It raises
        `KeyError` if the key does not exist. It is possible to use
        the sugar syntax of `del sdelPool[key]` instead.
        """
        del self._items[__key]
        self.UnscheduleDel(__key)
        del self._timers[__key]

    def ScheduleDel(self, key: ID) -> None:
        """Schedules a key for deletion. If it is already scheduled,
        it resets scheduling.
        """
        import asyncio
        self.UnscheduleDel(key)
        loop = asyncio.get_running_loop()
        self._timers[key] = loop.call_at(
            self._DEL_TIMINT,
            self._DeleteKey,
            key)

    def UnscheduleDel(self, key: ID) -> None:
        """Unschedules a key for deletion. If it has not scheduled, it
        has no eefect.
        """
        if key in self._timers:
            self._timers[key].cancel()
            if not self._timers[key].cancelled():
                logging.fatal('E1-1', exc_info=True)
            self._timers[key] = None


class LSDelPool(SDelPool[_SDelType]):
    """
    #### Loadable SDelPool
    Objects of this type act like `SDelPool` but upon failure in
    access, it tries to load the object via `Load` method.
    """
    def __init__(self, db: IDatabase) -> None:
        super().__init__()
        self._db = db
        """The database object"""
    
    @abstractmethod
    def Load(self, key: ID) -> _SDelType:
        """Loads member object when the key is not available. If it cannot
        load the member object, it must raise `KeyError` exception.
        """
        pass

    @abstractmethod
    def Save(self, key: ID) -> None:
        """Saves the member object just before deletion. If it cannot
        load the member object, it must throws `KeyError` exception.
        """
        pass

    def _GetKey(self, __key: ID, /) -> _SDelType:
        try:
            item = super()._GetKey(__key)
        except KeyError:
            item = self.Load(__key)
        return item

    def _DeleteKey(self, __key: ID, /) -> None:
        self.Save(__key)
        super()._DeleteKey(__key)


class Users(LSDelPool[UserData]):
    def Load(self, key: int) -> UserData:
        userData = self._db.GetUser(key)
        if userData is None:
            raise KeyError()
        return userData


class AbsOperation(ABC):
    """Abstract base class for operations in the Bot. Objects of this
    type supports the followings:

    1. hash protocol
    2. equality comparison
    """
    _nId = 0
    """This attribute is used to produce unique id in `GenerateUid` class
    method.
    """

    @classmethod
    def GenerateUid(cls) -> int:
        """Produces a unique id. This uniqueness is guaranteed among
        all instances of this class.
        """
        hash_ = cls._nId
        cls._nId += 1
        if cls._nId > 0xff_ff_ff_ff:
            cls._nId = 0
        return hash_
    
    def __init__(self) -> None:
        self._uid = AbsOperation.GenerateUid()
        """The unique ID of this instance."""
    
    def __hash__(self) -> int:
        return self._uid

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, AbsOperation):
            return self._uid == __obj._uid
        return NotImplemented
    
    @property
    def Uid(self) -> int:
        """Returns the unique ID of this object."""
        return self._uid
    
    def CancelByCmd(
            self,
            message: Message,
            cmd: str
            ) -> tuple[Coroutine[Any, Any, Message] | None, bool]:
        """Optionally returns a reply for the passed in command and
        specifies whether the whole operation has finished or not.
        """
        buttons = InlineKeyboardMarkup()
        buttons.add(InlineKeyboardButton(
            lang.CONTINUE_OP,
            callback_data=f'{self.Uid}-2'))
        buttons.add(InlineKeyboardButton(
            lang.CANCEL_OP,
            callback_data=f'{self.Uid}-1-{cmd}'))
        return message.reply(lang.DISRUPTIVE_CMD, components=buttons), False

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
        # Turning 'cb' into [int, optional]...
        parts = cb.split('-')
        try:
            parts[0] = int(parts[0])
        except IndexError:
            logging.error('E1-3')
            return
        except ValueError:
            logging.error('E1-4')
            return
        # Replying callback...
        match parts[0]:
            case self.CONTINUE_CB:
                return None, False
            case self.CANCELED_BY_CMD_CB:
                pass


class SigninOp(AbsOperation):
    """Encapsulates a sign-in operation in the Bot. You should start
    this operation by calling `Start` method.
    """
    def __init__(self) -> None:
        super().__init__()
        self._firstName: str | None = None
        self._lastName: str | None = None
        self._phone: str | None = None

    def Start(
            self,
            message: Message
            ) -> Coroutine[Any, Any, Message]:
        return message.reply(lang.ENTER_YOUR_FIRST_NAME)

    def ReplyText(
            self,
            message: Message,
            text: str,
            ) -> Coroutine[Any, Any, Message]:
        """Gets from user and fills folowing items in consecutive calls:
        1. first name
        2. last name
        3. e-mail
        4. phone no.
        """
        if self._firstName is None:
            self._firstName = text
        elif self._lastName is None:
            self._lastName = text
        elif self._phone is None:
            self._phone = text
        else:
            logging.error()

    def ReplyCallback(
            self,
            message: Message,
            cb: str,
            ) -> Coroutine[Any, Any, Message]:
        super().ReplyCallback(message, cb)


class OpPool(SDelPool[AbsOperation]):

    CANCELED_BY_CMD_CB = 1
    """The infix of the callback data denotes cancelation of this
    operation by a command. The callback data must have this format:
    `<uid>-1-/<cmd>`
    """

    CONTINUE_CB = 2
    """The suffix of the callback data which denotes that this operation
    to be continued. The callback data must have this format:
    `<uid>-2`
    """

    def __init__(self) -> None:
        super().__init__()

    def GetTextReply(
            self,
            message: Message,
            user: User,
            text: str,
            ) -> Coroutine[Any, Any, Message] | None:
        """Gets the optional reply of the user provided text. It raises
        `KeyError` if the user does not have an ongoing operation.
        """
        reply, finished = self[user.id].ReplyText(message, text)
        if finished:
            self.DelItem(user.id)
        return reply

    def GetCallbackReply(
            self,
            message: Message,
            user: User,
            cb: str,
            ) -> Coroutine[Any, Any, Message] | None:
        """Gets the optional reply of the callback. It raises
        `KeyError` if the user does not have an ongoing operation.
        """
        reply, finished = self[user.id].ReplyCallback(message, cb)
        if finished:
            self.DelItem(user.id)
        return reply
    
    def CancelByCmdReply(
            self,
            message: Message,
            user: User,
            cmd: str,
            ) -> Coroutine[Any, Any, Message] | None:
        """It raises
        `KeyError` if the user does not have an ongoing operation.
        """
        # Checking if the user has an ongoing operation...
        self._items[user.id]
        # Asking for cancelation...
        buttons = InlineKeyboardMarkup()
        buttons.add(InlineKeyboardButton(
            lang.CONTINUE_OP,
            callback_data=f'{self.Uid}-2'))
        buttons.add(InlineKeyboardButton(
            lang.CANCEL_OP,
            callback_data=f'{self.Uid}-1-{cmd}'))
        return message.reply(lang.DISRUPTIVE_CMD, components=buttons), False
