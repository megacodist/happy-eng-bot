import logging
import os


def foo(bar: list = []) -> None:
    print(locals())
    bar.append(None)
    print(locals())
    print('-' * 10)
 
if __name__ == '__main__':
    logger = logging.getLogger()
    fileHandler = logging.FileHandler(
        filename=r'd:\bjbd',
        mode='a')
    fileHandler.setLevel(logging.INFO)
    consoleHandler = logging.StreamHandler()
    baz = []
    foo()
    foo()
    foo()
    foo(baz)
    foo()
    print(baz)