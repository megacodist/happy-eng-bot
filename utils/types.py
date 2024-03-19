#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Commands`
"""

import enum


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
