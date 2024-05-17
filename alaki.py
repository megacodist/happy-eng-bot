#
# 
#
from abc import ABC, abstractmethod
from datetime import date, timedelta
from functools import partial
from collections.abc import Awaitable, Coroutine
from typing import Any


def main() -> None:
    import gettext
    from utils.funcs import Foo
    Foo('main', 'locales', 'en')
    print(_('LANG'))
    print(_('SELECT_LANG'))
    Foo('alaki', 'locales', 'en')
    print(_('ALAKI'))
    

if __name__ == '__main__':
    main()