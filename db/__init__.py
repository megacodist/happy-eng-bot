#
# 
#
"""This sub-package offers database-related functionalities."""

from abc import ABC, abstractmethod


type ID = int
"""Instaces of `ID` type are, of course, integers but had better treat
as IDs of users or products in the database.
"""


class HourlyFrequencies:
    """Instances of this class hold frequencies (integers) for all 24
    hours of a day (from 0 to 23 inclusive). You can specifies the length
    of these frequencies, otherwise two bytes is the default.

    Normalization: when at least one of the frequencies exceeds the
    limit, all values will be normalized, i.e. all frequencies will
    be devided by two until all of them fulfill the length limit.
    
    This class is NOT thread-safe.
    """

    @classmethod
    def GetMax(cls, n: int) -> int:
        """Gets maximum frequency for the specified number of bytes."""
        if not isinstance(n , int):
            raise TypeError("number of bytes must be an integer not "
                f"'{type(n).__class__.__name__}'")
        if n <= 0:
            raise ValueError("number of bytes must be positive")
        max_ = 0xff
        idx = 1
        while idx < n:
            max_ = max_ << 8
            max_ |= 0xff
            idx += 1
        return max_

    def __init__(self, *, bytes_count = 2) -> None:
        """Initializes a new instance of this type:
        * `bytes_count`: the length of each frequency
        """
        self._nBytes = bytes_count
        """The length of each frequency when it comes to `bytes`
        conversions.
        """
        self._max = HourlyFrequencies.GetMax(bytes_count)
        """Specifies the maximum value for each frequency according to the
        length.
        """
        self._freqs = [0] * 24
        """A list of 24 integers for number of access in each hour."""
    
    def __repr__(self) -> str:
        hoursFreqs = ', '.join(
            f'{hour}={freq}'
            for hour, freq in enumerate(self._freqs))
        return (f"<'{self.__class__.__qualname__}' object, "
            f"frequencies={hoursFreqs}>")
    
    def __getitem__(self, __hour: int, /) -> int:
        self.GetHourFreq(__hour)
    
    def __setitem__(self, __hour: int, __freq: int, /) -> None:
        self.SetHourFreq(__hour, __freq)
    
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
        noShiftCheck = True if __n >= self._nBytes else False
        self._nBytes = __n
        self._max = HourlyFrequencies.GetMax(__n)
        if noShiftCheck:
            return
        # Normalizing if necessary...
        n = 0
        for idx in range(24):
            n = max(self._GetExtraBits(self._freqs[idx]), n)
        if n:
            self._ShiftFreqs(n)
    
    @property
    def Bytes(self) -> bytes:
        """Gets or sets the access frequencies as serialized (raw) data.
        Suitable for I/O operations. If provided bytes object is less than
        necessary, the remaining part is filled with zeros, or If it is
        larger than necessary, the additional part will be ignored.
        """
        from io import BytesIO
        with BytesIO() as bufferObj:
            for freq in self._freqs:
                bufferObj.write(freq.to_bytes(self._nBytes))
            buffer = bufferObj.getvalue()
        return buffer
    
    @Bytes.setter
    def Bytes(self, __buf: bytes) -> None:
        from io import BytesIO
        with BytesIO(__buf) as bufObj:
            for idx in range(24):
                self._freqs[idx] = int.from_bytes(bufObj.read(self._nBytes))
    
    @property
    def Frequencies(self) -> tuple[int, ...]:
        """Gets a 24-tuple of hourly access frequnecies."""
        return tuple(self._freqs)
    
    def GetHourFreq(self, __hour: int, /) -> int:
        """Gets the frequency of the specified hour. The sugar syntax of
        item access (`freq = hourlyFreqs[hour]`) is also supported.

        #### Exceptions:
        * `TypeError`: the argument is not an integer
        * `IndexError`: hours must be 0<= hour <= 23
        """
        try:
            return self._freqs[__hour]
        except TypeError as err:
            err.args = ('hour must be an inteher not '
                f'{__hour.__class__.__qualname__}',)
            raise err
        except IndexError as err:
            err.args = ('hours must be between 0 and 23 inclusive',)
            raise err 
    
    def SetHourFreq(self, __hour: int, __freq: int, /) -> None:
        """Sets the frequency of the specified hour. The sugar syntax of
        item access (`hourlyFreqs[hour] = freq`) is also supported.

        #### Exceptions:
        * `TypeError`: the hour argument is not an integer
        * `IndexError`: hours must be 0<= hour <= 23
        """
        if not isinstance(__freq, int):
            raise TypeError('frequency of an hour must be an integer not '
                f'{__freq.__class__.__qualname__}')
        try:
            self._freqs[__hour] = __freq
        except TypeError as err:
            err.args = ('hour must be an inteher not '
                f'{__hour.__class__.__qualname__}',)
            raise err
        except IndexError as err:
            err.args = ('hours must be between 0 and 23 inclusive',)
            raise err
        # Normalizing if necessary...
        n = self._GetExtraBits(__freq)
        if n:
            self._ShiftFreqs(n)
    
    def Increment(self, __hour: int, /) -> None:
        """Increments the specified hour, normalizes if necessary."""
        self.SetHourFreq(__hour, self.GetHourFreq(__hour) + 1)
    
    def _ShiftFreqs(self, __n: int, /) -> None:
        """Shifts all frequencies `n` bits. For positive integers this
        shift is to the right, for negatives to the left, and for zero
        nothing happens.
        """
        if not isinstance(__n, int):
            raise TypeError("for shifting bits an integer is required "
                f"not '{type(__n).__name__}'")
        if __n > 0:
            for idx in range(24):
                self._freqs[idx] = self._freqs[idx] >> __n
        elif __n < 0:
            __n = -__n
            for idx in range(24):
                self._freqs[idx] = self._freqs[idx] << __n
    
    def _GetExtraBits(self, __num: int, /) -> None:
        """Returns the number of extra bits of the provided number compared
        to the established length of these frequencies.
        """
        n = 0
        while __num >= self._max:
            n += 1
            __num = __num >> 1
        return n


class UserData:
    """This data structure contains information associated with a typical
    user of the Bot.

    #### Characteristics
    * Hash protocol: instances are hashable.
    * Equality comparison
    """
    def __init__(
            self,
            id: ID,
            first_name: str,
            last_name: str,
            phone: str,
            freqs: HourlyFrequencies | None = None,
            ) -> None:
        self._id = id
        self._firstName = first_name
        self._lastName = last_name
        self._phone = phone
        self._hFreqs = freqs if freqs else HourlyFrequencies()
    
    def __eq__(self, __other, /) -> bool:
        if not isinstance(__other, self.__class__):
            return NotImplemented
        return self._id == __other._id
    
    def __hash__(self) -> int:
        return self._id
    
    def __repr__(self) -> str:
        return (
            f"<'{self.__class__.__qualname__}' object; ID={self._id}; "
            f"first name={self._firstName}; last name={self._lastName}; "
            f"phone={self._phone}; hourly access frequencies={self._hFreqs}>")
    
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
    def Frequencies(self) -> HourlyFrequencies:
        """Gets hourly access frequencies."""
        return self._hFreqs
    
    def AsTuple(self) -> tuple[int, str, str, str, bytes]:
        return (
            self._id,
            self._firstName,
            self._lastName,
            self._phone,
            self._hFreqs.Bytes)


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
    def UpsertUser(self, user_data: UserData) -> None:
        """Updates the specified user in the users table or if the user
        does not exist in the tablt, it will insert it.
        """
        pass

    @abstractmethod
    def DoesIdExist(self, __id: int) -> bool:
        """Specifies whether an ID exists in the database or not."""
        pass

