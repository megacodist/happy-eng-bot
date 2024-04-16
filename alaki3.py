#
# 
#

import asyncio
from collections import deque
from importlib import import_module
from pathlib import Path


def main() -> None:
    modsDir = Path(__file__).resolve().parent / 'cmds'
    modNames = [
        modName.stem
        for modName in modsDir.glob('*.py')]
    try:
        modNames.remove('__init__')
    except ValueError:
        pass
    print(modNames)
    for modName in modNames:
        modObj = import_module(f'cmds.{modName}')
        print(modObj)


if __name__ == '__main__':
    main()
