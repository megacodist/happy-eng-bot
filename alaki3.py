#
# 
#

import asyncio
from collections import deque
from importlib import import_module
from pathlib import Path
from typing import Awaitable

var = [1,]


async def Foo() -> None:
    pass


def main() -> None:
    foo = Foo()
    print(isinstance(foo, Awaitable[None]))


if __name__ == '__main__':
    main()
