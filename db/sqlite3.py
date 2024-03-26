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
    
    def Close(self) -> None:
        """Closes the database."""
        self._conn.close()
    
    def GetAllUserIds(self) -> tuple[int, ...]:
        sql = "SELECT user_id FROM users"
        cur = self._conn.cursor()
        cur = cur.execute(sql)
        return tuple(cur)
    
    def DoesIdExist(self, __id: int) -> bool:
        return __id in self.GetAllUserIds()
