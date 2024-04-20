#
# 
#

from datetime import date, timedelta


class Foo(object):
    def __getitem__(self, __val1, /) -> None:
        print(__val1,)


def Baz() -> None:
    pass


def main() -> None:
    from collections import deque
    from random import randint, random
    q = deque()
    for _ in range(randint(0, 100)):
        q.append(random())
    while q:
        print(q.popleft())


if __name__ == '__main__':
    main()