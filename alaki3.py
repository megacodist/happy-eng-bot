#
# 
#

import asyncio
from typing import Any, Callable


def main() -> None:
    import sqlite3
    from utils.types import LSDelPool
    conn = sqlite3.connect(r'db.db3')
    objPool = LSDelPool(conn)
    objPool.Save(12)


if __name__ == '__main__':
    main()
