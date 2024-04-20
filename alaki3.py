#
# 
#

import asyncio
from collections import deque
from importlib import import_module
from pathlib import Path

var = [1,]


def main() -> None:
    import alaki2
    global var
    print(var)
    alaki2.InitModule(var)
    print(var)


if __name__ == '__main__':
    main()
