#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Commands`
"""

from abc import ABC, abstractmethod
from asyncio import sleep, TimerHandle
import enum
import logging
from typing import Any, Callable, Coroutine, TypeVar

from bale import Message

from db import IDatabase


ID = int
"""The ID of a user in the Bale."""


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
