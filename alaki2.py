#
# 
#

from collections import namedtuple
import sqlite3

from db import UserData, HourlyFrequencies


def main() -> None:
    updInsSql = """
            INSERT OR REPLACE INTO
                users(user_id, first_name, last_name, phone, hourly_freqs)
            VALUES
                (?, ?, ?, ?, ?);
        """
    selSql = """
        SELECT
            user_id, first_name, last_name, phone, hourly_freqs
        FROM
            users;
    """
    with sqlite3.connect('db.db3') as conn:
        cur = conn.cursor()
        cur = cur.execute(selSql)
        print('All products ===================')
        users: list[UserData] = []
        for user in cur.fetchall():
            hFreqs = HourlyFrequencies()
            hFreqs.Bytes = user[4]
            users.append(UserData(*user[:4], hFreqs))
            print(users[-1])
        print(users[-1].AsTuple())

        users[-1]._phone = '9377472900'
        cur = conn.cursor()
        cur = cur.execute(updInsSql, users[-1].AsTuple())
        cur = cur.execute(selSql)
        print('All users ===================')
        for user in cur.fetchall():
            print(user)


def main2() -> None:
    selSql = """
        SELECT
            prod_id, prod_name
        FROM
            products;
    """
    upsertSql = """
        INSERT OR REPLACE INTO
            products (prod_id, prod_name)
        VALUES
            (100100, 'Salam');
    """
    with sqlite3.connect('db.db3') as conn:
        cur = conn.cursor()
        cur = cur.execute(selSql)
        print('All products ======================')
        for prod in cur:
            print(prod)
        cur = conn.cursor()
        cur = cur.execute(upsertSql)


if __name__ == '__main__':
    main()
