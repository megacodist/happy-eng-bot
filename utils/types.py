#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Commands`
"""

import enum
from typing import Any


class Commands(enum.Enum):
    """This enumeration contains all the supported commands of this Bot.
    The value of each enumerator is its shell command.
    """
    ADMIN = '/admin'
    HELP = '/help'
    MY_COURSES = '/mycourses'
    PRODUCTS = '/products'
    SIGN_IN = '/signin'
    START = '/start'


class UserData:
    def __init__(self) -> None:
        pass


class Users:
    def __init__(self) -> None:
        self._users: dict[int, Any] = {}
