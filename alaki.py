#
# 
#

from datetime import date, timedelta


class Foo(object):
    def __getitem__(self, __val1, /) -> None:
        print(__val1,)


def main() -> None:
    interval = timedelta(seconds=-1)
    print(interval)
    date_ = date.today()
    print(date_.toordinal())


if __name__ == '__main__':
    b = Foo()
    b[1, 2]
