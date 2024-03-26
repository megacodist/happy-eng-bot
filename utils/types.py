#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Commands`
"""

from abc import ABC, abstractmethod
from asyncio import sleep, TimerHandle
import enum
from typing import Any, Generic, TypeVar
import logging
from typing import Any, Callable, Coroutine, TypeVar

from bale import Message

from db import IDatabase
import lang


ID = int
"""Instaces of `ID` type are, of course, integers but has better treat
as IDs of users' in Bale.
"""


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
    """Specifies the types of input the end user can enter."""
    TEXT = 0
    CALLBACK = 1


_SDelType = TypeVar('_SDelType')
"""The type of member objects inside of an `SDelPool` object."""

class SDelPool(Generic[_SDelType]):
    """
    ### Deletion-scheduled pool of objects

    An object of this class is a pool of member objects accessible via
    keys. Memeber objects are scheduled for deletion after each access
    and get deleted after a specified amount of time if they do not access
    any more. This scheduling happens on `asyncio`.

    #### Operators:
    1. Getting an item with a key (`a = sdelPool[key]`)
    2. Setting an item with a key (`sdelPool[key[key] = a`)
    3. Deleting an item with a key (`del sdelPool[key]`)
    """
    def __init__(self, id: ID) -> None:
        """Initializes a new instance of this type with the folowing:

        * `id`: the ID of the user.
        """
        from asyncio import TimerHandle
        self._DEL_TIMINT = 3_600
        """The time interval for deletion in seconds."""
        self._id = id
        """The ID of the user who initiate the operation."""
        self._items: dict[ID, _SDelType] = {}
        self._timers: dict[ID, TimerHandle] = {}
    
    def __getitem__(self, __key: ID, /) -> _SDelType:
        item = self._items[__key]
        self.ScheduleDel(__key)
        return item

    def __setitem__(self, __key: ID, __value: _SDelType, /) -> None:
        self._items[__key] = __value
        self.ScheduleDel(__key)

    def __delitem__(self, __key: ID, /) -> None:
        del self._items[__key]
        self.UnscheduleDel(__key)

    def _DeleteKey(self, __key: ID, /) -> None:
        del self._items[__key]
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


class AbsOperation(ABC):
    """Abstract base class for operations in the Bot. Objects of this
    type supports the followings:

    1. hash protocol
    2. equality comparison
    """
    _nHash = 0
    """This attribute is used to produce unique hash in
    `GetUniqueHash` class method"""

    @classmethod
    def GetUniqueHash(cls) -> int:
        """Produces a unique hash. This uniqueness is guaranteed among
        all instances of this class.
        """
        hash_ = cls._nHash
        cls._nHash += 1
        if cls._nHash > 0xff_ff_ff_ff:
            cls._nHash = 0
        return hash_
    
    def __init__(self) -> None:
        self._hash = AbsOperation.GetUniqueHash()
        """The hash of this object."""
    
    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, AbsOperation):
            return self._hash == __obj._hash
        return NotImplemented

    @abstractmethod
    def ReplyText(
            self,
            message: Message,
            text: str,
            ) -> Coroutine[Any, Any, Message]:
        """Replies the provided text."""
        pass

    @abstractmethod
    def ReplyCallback(
            self,
            message: Message,
            cb: str,
            ) -> Coroutine[Any, Any, MemoryError]:
        """Replies the callback."""
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
            ) -> Coroutine[Any, Any, MemoryError]:
        pass


class UserData:
    def __init__(
            self,
            first_name: str,
            last_name: str,
            email: str,
            phone_num: str,
            ) -> None:
        self._firstName = first_name
        self._lastName = last_name
        self._email = email
        self._phoneNum = phone_num
    
    @property
    def FirstName(self) -> str:
        return self._firstName
    
    @property
    def LastName(self) -> str:
        return self._lastName
    
    @property
    def Email(self) -> str:
        return self._email
    
    @property
    def PhoneNum(self) -> str:
        return self._phoneNum


class Users:
    """This data structure manages and holds information of recent users
    of the Bot.
    """
    def __init__(self, db: IDatabase) -> None:
        self._db = db
        """The database of the Bot."""
        self._users: dict[ID, UserData] = {}
        """The mapping of all recent users of the Bot."""
    
    def __getitem__(self, __id: ID, /) -> UserData:
        try:
            return self._users[__id]
        except KeyError:
            pass
