#
# 
#
from abc import ABC, abstractmethod
from datetime import date, timedelta
from functools import partial
from collections.abc import Awaitable, Coroutine
from typing import Any


def Foo(a: int, b: int, c: int) -> int:
    return a + b + c

async def Baz(a: int, b: int, c: int) -> int:
    return a + b + c


def main() -> None:
    aaa: Awaitable[int] = Baz(1, 2, 3)
    bbb: partial[Awaitable[int]] = partial(Baz, 2)

if __name__ == '__main__':
    main()