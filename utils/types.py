#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Commands`
"""

from abc import ABC, abstractmethod
from asyncio import sleep, TimerHandle
import enum
from typing import Any, TypeVar
import logging
from typing import Any, Callable, Coroutine, TypeVar

from bale import Message

from db import IDatabase


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


_SDelType = TypeVar('_SDelType')
class SDelPool:
    """
    ### Deletion-scheduled pool of objects

    An object of this class is a pool of objects accessible via keys.
    Elements are scheduled for deletion after each access and get
    deleted after a specified amount of time. This scheduling happens
    on `asyncio`.

    #### Operators:
    1. Getting an item with a key (`a = sdelPool[key]`)
    2. Setting an item with a key (`sdelPool[key[key] = a`)
    3. Deleting an item with a key (`del sdelPool[key]`)
    """
    def __init__(self) -> None:
        from asyncio import TimerHandle
        self._DEL_TIMINT = 3_600
        """The time interval for deletion in seconds."""
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


class AutoDelObj:
    _POLLING_CANCEL_DELAY = 0.1
    """The time interval at which to poll for deletion cancelation."""

    _MAX_POLLING = 10
    """Maximum number of polling for deletion cancelation."""

    def __init__(
            self,
            callback: Callable[[str], Coroutine[Any, Any, Message]]
            ) -> None:
        self._callback = callback
        self._timer: TimerHandle | None = None
        """The timer object of the pending deletion."""
    
    async def __call__(self, text: str) -> Coroutine[Any, Any, None]:
        if self._timer:
            self._timer.cancel()
            idx = 0
            while not self._timer.cancelled():
                await sleep(AutoDelObj._POLLING_CANCEL_DELAY)
                idx += 1
                if idx > AutoDelObj._MAX_POLLING:
                    logging.fatal('E1-1')
                    return


_T = TypeVar('_T')

class DeletablePool(ABC):
    def __init__(self, db: IDatabase) -> None:
        self._db = db
        """The database object of the Bot."""
        self._items: dict[ID, _T] = {}
    
    def __getitem__(self, __id: ID, /) -> Any:
        """Returns the data associated with the provided `ID` or otherwise
        if no such `ID` in the database, raises `KeyError`.
        """
        try:
            data = self._items[__id]
        except KeyError as err:
            data = self.Load(__id)
            if data:
                self._items[__id] = data
            else:
                raise err
        return data
    
    @abstractmethod
    def Load(self, __id: ID, /) -> _T | None:
        pass
    
    def ScheduleDel(self) -> None:
        pass
    
    def UnscheduleDel(self) -> None:
        pass

    def RescheduleDel(self) -> None:
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
