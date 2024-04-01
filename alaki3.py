def AppendOne(lst: list[int] = []) -> list[int]:
    lst.append(1)
    return lst


if __name__ == '__main__':
    lst = [1, 2,]
    print(f'{AppendOne.__name__}.__defaults__:', AppendOne.__defaults__)
    print(f'{AppendOne.__name__} output:      ', AppendOne(lst))
    print(f'{AppendOne.__name__}.__defaults__:', AppendOne.__defaults__)
    print(f'{AppendOne.__name__} output:      ', AppendOne())
    print(f'{AppendOne.__name__}.__defaults__:', AppendOne.__defaults__)
    print(f'{AppendOne.__name__} output:      ', AppendOne())
    print(f'{AppendOne.__name__}.__defaults__:', AppendOne.__defaults__)
    print('\523')
