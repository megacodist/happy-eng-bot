#
# 
#
"""This module realizes the `IDatabase` interface on top of Python
Sqlite3. This module only offers `SqliteDb` class."""

from os import PathLike
import sqlite3

from db import UserData

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
    
    def GetUser(self, __id: int) -> UserData | None:
        sql = """
            SELECT
                user_id, first_name, last_name, phone, frequencies
            FROM
                users
            WHERE
                user_id = ?;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (__id,))
        res = cur.fetchone()
        if res is None:
            return None
        return UserData(res[0], res[1], res[2], res[3], res[4])
    
    def UpdateUser(self, user_data: UserData) -> None:
        sql = """
            UPDATE
                users
            SET
                first_name = ?,
                last_name = ?,
                phone = ?,
                frequencies = ?
            WHERE
                user_id = ?;
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (user_data.FirstName, user_data.LastName, user_data.Phone))
    
    def DoesIdExist(self, __id: int) -> bool:
        sql = """
            SELECT
                EXISTS(
                    SELECT 1
                    FROM users
                    WHERE user_id=?);
        """
        cur = self._conn.cursor()
        cur = cur.execute(sql, (__id,))
        return bool(cur.fetchone()[0])
