#
# 
#
"""This sub-package offers database-related functionalities."""

from abc import ABC, abstractmethod


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
    def DoesIdExist(self, __id: int) -> bool:
        """Specifies whether an ID exists in the database or not."""
        pass

