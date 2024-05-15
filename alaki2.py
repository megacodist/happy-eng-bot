#
# 
#
from __future__ import annotations
from collections import defaultdict, deque
import enum
from queue import Queue
from threading import Thread, RLock
from typing import Any


class Spsc(enum.IntEnum):
    """This enumeration offers choices of Roch, Paper, Scissors game.
    This class implements hashable and rich comparisonprotocols.
    """
    STONE = 1
    PAPER = 2
    SCISSORS = 3

    @classmethod
    def getComparer(cls, a: Spsc, b: Spsc) -> int:
        """If the return is:
        * positive: `a > b`
        * 0: `a == b`
        * negative: `a < b`
        """
        dif = a.value - b.value
        return dif * ((-1) ** (abs(dif) - 1))

    def getDefier(self) -> Spsc:
        """Gets the enumerator that defies this one."""
        match self:
            case Spsc.STONE:
                return Spsc.PAPER
            case Spsc.PAPER:
                return Spsc.SCISSORS
            case Spsc.SCISSORS:
                return Spsc.STONE
    
    def getLoser(self) -> Spsc:
        """Gets the enumerator that loses this one."""
        match self:
            case Spsc.STONE:
                return Spsc.SCISSORS
            case Spsc.PAPER:
                return Spsc.STONE
            case Spsc.SCISSORS:
                return Spsc.PAPER

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.getDefier() == other
    
    def __le__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.getLoser() != other
    
    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.getLoser() == other
    
    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.getDefier() != other
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value == other.value
    
    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value != other.value
    
    def __hash__(self) -> int:
        return self.value


choices = deque[Spsc]()


class ComChoiceThrd(Thread):
    def __init__(self) -> None:
        super().__init__(
            group=None,
            target=None,
            name='Computer choice',
            daemon=False,)
        self._choice: Spsc | None = None
        self._mutex = RLock()
    
    @property
    def choice(self) -> Spsc:
        """Gets the computer choice of `Stone`, `Paper` or `Scissors` or
        raises  `ValueError` if the decision has not been made.
        """
        self._mutex.acquire()
        choice = self._choice
        self._mutex.release()
        if choice is None:
            raise ValueError()
        else:
            return choice
    
    def _setChoice(self, choice: Spsc) -> None:
        self._mutex.acquire()
        self._choice = choice
        self._mutex.release()
    
    def _run(self) -> None:
        pass
        
    def run(self) -> None:
        # Declaring of variables --------------------------
        import random
        global choices
        # Functioning -------------------------------------
        predicts: dict[Spsc, int] = defaultdict(lambda: 0)
        if len(choices) >= 5:
            map_ = self._qToDict(choices, slice(-5, None))
            res = self._decide(map_, 5)
            if isinstance(res, Spsc):
                self._setChoice(res.getDefier())
                return
            elif isinstance(res, tuple):
                for spsc in res:
                    predicts[spsc] += 1
        if len(choices) >= 10:
            map_ = self._qToDict(choices, slice(-10, -5), map_)
            res = self._decide(map_, 10)
            if isinstance(res, Spsc):
                self._setChoice(res.getDefier())
                return
            elif isinstance(res, tuple):
                for spsc in predicts:
                    predicts[spsc] += 1
                for spsc in res:
                    predicts[spsc] += 1
        if len(choices) >= 20:
            for n in range(20, len(choices), 10):
                map_ = self._qToDict(choices, slice(-n, -n + 10), map_)
                res = self._decide(map_, n)
                if isinstance(res, Spsc):
                    for spsc in predicts:
                        predicts[spsc] += 1
                    predicts[res] += 1
                elif isinstance(res, tuple):
                    for spsc in predicts:
                        predicts[spsc] += 1
                    for spsc in res:
                        predicts[spsc] += 1
        for spsc in Spsc:
            predicts[spsc] += 1
        weights = [predicts[spsc] for spsc in Spsc]
        guess = random.choices(list(Spsc), weights, k=1)[0]
        self._setChoice(guess.getDefier())

    def _qToDict(
            self,
            q: deque[Spsc],
            slice_: slice,
            map_: dict[Spsc, int] | None = None,
            ) -> dict[Spsc, int]:
        """Converts queue of user choices into a mapping of
        `Spsc -> number of choices`. if `map_` is provided, it will be
        updated with the new slice of the queue. Otherwise `map_` will
        be created, intialized and returned.
        """
        if map_ is None:
            map_ = defaultdict(lambda: 0)
        lst = list(q)[slice_]
        for elem in lst:
            map_[elem] += 1
        return map_
    
    def _decide(
            self,
            map_: dict[Spsc, int],
            sum_: int,
            ) -> None | Spsc | tuple[Spsc] | tuple[Spsc, Spsc]:
        highFreq: list[Spsc] = []
        for elem in map_:
            freq = map_[elem] / sum_
            if freq >= 0.65:
                return elem
            elif freq >= 0.4:
                highFreq.append(elem)
        if len(highFreq) > 0:
            return tuple(highFreq) # type: ignore


def main() -> None:
    # Declaring of variables ------------------------------
    global choices
    # Functioning -----------------------------------------
    uScore = 0
    cScore = 0
    while True:
        choiceThrd = ComChoiceThrd()
        choiceThrd.start()
        print(f'You {uScore}:{cScore} Computer')
        for item in Spsc:
            print(f'\t{item.value}. {item.name.capitalize()}')
        input_ = input('Select your choice (ctrl+C to exit): ')
        try:
            uChoice = Spsc(int(input_))
        except ValueError:
            try:
                uChoice = Spsc[input_.upper()]
            except KeyError:
                print(f'Invalid input: {input_}')
                continue
        # Determining the winner...
        try:
            cChoice = choiceThrd.choice
        except ValueError :
            choiceThrd.join()
            cChoice = choiceThrd.choice
        print(f'Your choice: {uChoice.name.capitalize()}')
        print(f'Computer choice: {cChoice.name.capitalize()}')
        if uChoice > cChoice:
            uScore += 1
            print('\tYou won!!!')
        elif  uChoice < cChoice:
            cScore += 1
            print('\tYou lost!!!')
        else:
            print('\tDraw')
        # Saving current user choice...
        choices.append(uChoice)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
