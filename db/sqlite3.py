#
# 
#
"""This module realizes the `IDatabase` interface on top of Python
Sqlite3. This module only offers `SqliteDb` class."""

from os import PathLike
import sqlite3

from . import IDatabase


class SqliteDb(IDatabase):
    def __init__(self, db_file: PathLike) -> None:
        """Initializes a new database instance from the provided path."""
        self._conn = sqlite3.connect(db_file)
        """The connection object of the database."""
    
    def GetAllUserIds(self) -> tuple[int, ...]:
        sql = "SELECT ID FROM Users"
        cur = self._conn.cursor()
        cur = cur.execute(sql)
        return tuple(cur)
