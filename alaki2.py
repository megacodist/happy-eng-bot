#
# 
#

from collections import namedtuple
import sqlite3

from db import UserData, HourlyFrequencies


a: list[int]


def InitModule(a_: list[int]) -> None:
    global a
    a = a_
    a.append(2)


def main() -> None:
    pass


if __name__ == '__main__':
    main()
