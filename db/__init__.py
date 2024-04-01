#
# 
#
"""This sub-package offers database-related functionalities."""

from abc import ABC, abstractmethod


type ID = int
"""Instaces of `ID` type are, of course, integers but had better treat
as IDs of users or products in the database.
"""


class AccessFrequencies:
    """
    This class is NOT thread-safe.
    """

    def __init__(self, *, bytes_count = 2) -> None:
        """Initializes a new instance of this type:
        * `bytes_count`: the length of each frequency
        """
        self._nBytes = bytes_count
        """The length of each frequency when it comes to `bytes`
        conversions.
        """
        self._freqs = [0] * 24
        """A list of 24 integers for number of access in each hour."""
    
    def __repr__(self) -> str:
        return (f"<'{self.__class__.__qualname__}' object, "
            f"frequencies={self._freqs}>")
    
    @property
    def BytesCount(self) -> int:
        """Gets or sets number of bytes (length) for each frequency."""
        return self._nBytes
    
    @BytesCount.setter
    def BytesCount(self, __n: int, /) -> None:
        if not isinstance(__n, int):
            raise TypeError('number of bytes must be a positive integer')
        if __n < 1:
            raise ValueError('number of bytes must be a positive integer')
        self._nBytes = __n
    
    @property
    def Bytes(self) -> bytes:
        """Gets or sets the access frequencies as serialized (raw) data.
        Suitable for I/O operations. If provided bytes object is less than
        necessary, the remaining part is filled with seros.
        """
        from io import BytesIO
        with BytesIO() as bufferObj:
            for freq in self._freqs:
                bufferObj.write(freq.to_bytes(self._nBytes))
            buffer = bufferObj.getvalue()
        return buffer
    
    @property
    def HourlyAccess(self) -> tuple[int, ...]:
        """Gets a 24-tuple of hourly access frequnecies."""
        return tuple(self._freqs)


class UserData:
    """This data structure contains information associated with a typical
    user of the Bot.
    """
    def __init__(
            self,
            id: ID,
            first_name: str,
            last_name: str,
            phone: str,
            freqs: bytes,
            ) -> None:
        self._id = id
        self._firstName = first_name
        self._lastName = last_name
        self._phone = phone
        self._freqs = AccessFrequencies()
        self._freqs.Bytes = freqs
    
    def __repr__(self) -> str:
        hourlyFreqs = ', '.join(
            f'{hour}:{freq}'
            for hour, freq in enumerate(self._freqs))
        return (
            f"<'{self.__class__.__qualname__}' object; ID={self._id}; "
            f"first name={self._firstName}>; last name={self._lastName}; "
            f"phone={self._phone}; hourly access frequencies={hourlyFreqs}")
    
    @property
    def Id(self) -> ID:
        return self._id
    
    @property
    def FirstName(self) -> str:
        return self._firstName
    
    @property
    def LastName(self) -> str:
        return self._lastName
    
    @property
    def Phone(self) -> str:
        return self._phone
    
    @property
    def Frequencies(self) -> AccessFrequencies:
        """Gets hourly access frequencies."""
        return self._freqs


class IDatabase(ABC):
    """This interface defines a blueprint to work with a database for
    the Bot.
    """
    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        """This initializer must connect to the database."""
        pass

    @abstractmethod
    def Close(self) -> None:
        """Closes the database."""
        pass

    @abstractmethod
    def GetAllUserIds(self) -> tuple[int, ...]:
        """Returns a tuple of all user IDs in the database."""
        pass

    @abstractmethod
    def GetUser(self, __id: ID) -> UserData | None:
        """Gets the information of the specified user in the database. It
        returns `None` if the user ID does not exist.
        """
        pass

    @abstractmethod
    def UpdateUser(self, user_data: UserData) -> None:
        """Updates the specified user in the users table."""
        pass

    @abstractmethod
    def DoesIdExist(self, __id: int) -> bool:
        """Specifies whether an ID exists in the database or not."""
        pass

