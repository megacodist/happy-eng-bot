from abc import abstractmethod
import logging
import os
from typing import TypeVar


_T = TypeVar('_T')
class Foo:
    def __init__(self) -> None:
        self._items: dict[int, _T] = {}

    @abstractmethod
    def Bar(self, __id: int, /) -> _T:
        pass


def foo(bar: list = []) -> None:
    print(locals())
    bar.append(None)
    print(locals())
    print('-' * 10)
 
if __name__ == '__main__':
    import tomllib
    with open(
            r'F:\Mohsen\Programming\Python\happy-eng-bot\config.toml',
            mode='rb') as fileObj:
        config = tomllib.load(fileObj)
    print(config)