#
# 
#

from dataclasses import dataclass

class Collection[T]:
    def __init__(self) -> None:
        self._items: list[T] = []
    
    def GetItem(self, __idx: int, /) -> T:
        return self._items[__idx]


@dataclass
class Person:
    name: str
    id: int


class People(Collection[Person]):
    pass


if __name__ == '__main__':
    people = People()
    people.GetItem
