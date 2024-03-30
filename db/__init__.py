#
# 
#
"""This sub-package offers database-related functionalities."""

from abc import ABC, abstractmethod


type ID = int
"""Instaces of `ID` type are, of course, integers but had better treat
as IDs of users or products in the database.
"""


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
            frequencies,
            ) -> None:
        self._id = id
        self._firstName = first_name
        self._lastName = last_name
        self._phone = phone
        self._frequencies = frequencies
    
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
    def Frequencies(self) -> None:
        pass


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

