import os

def foo(bar: list = []) -> None:
    print(locals())
    bar.append(None)
    print(locals())
    print('-' * 10)
 
if __name__ == '__main__':
    baz = []
    foo()
    foo()
    foo()
    foo(baz)
    foo()
    print(baz)