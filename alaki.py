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
    for obj in (Foo, Baz,):
        print(obj.__name__.ljust(70, '='))
        maxLen = max(len(attr) for attr in dir(obj))
        for attr in dir(obj):
            print(f'{attr:>{maxLen}}: {getattr(obj, attr)}')


if __name__ == '__main__':
    main()