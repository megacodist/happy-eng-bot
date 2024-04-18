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
    from importlib import import_module
    mods = ['basic',]
    for name in mods:
        module = import_module(f'cmds.{name}')


if __name__ == '__main__':
    main()