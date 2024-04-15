#
# 
#
"""This package ABCs and implementation of Bot commands."""


from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from bale import Message

from utils.types import ID


class Page:
    def __init__(
            self,
            cmd: str,
            callback: Callable[[ID], Message]) -> None:
        self.cmd = cmd
        self.callback = callback


class WizardRes:
    def __init__(
            self,
            reply: Coroutine[Any, Any, Message] | None,
            finished: bool,
            ) -> None:
        self.reply = reply
        self.finished = finished


class AbsWizard(ABC):
    """Abstract base class for operations in the Bot. Implementations
    must avoid returning replies directly but rather use `Reply` method.
    Objects of this type supports the followings:

    1. hash protocol
    2. equality comparison
    """
    _nId = 1
    """This attribute is used to produce unique id in `GenerateUid` class
    method.
    """

    CMD: str
    """The literal of this command."""

    @classmethod
    def GenerateUid(cls) -> int:
        """Generates a unique id. This uniqueness is guaranteed among
        all instances of this class even deleted ones.
        """
        uid = cls._nId
        cls._nId += 1
        if cls._nId > 0xff_ff_ff_ff:
            cls._nId = 1
        return uid
    
    def __init__(self) -> None:
        self._UID = self.GenerateUid()
        """The unique ID of this operation."""
        self._lastReply: Coroutine[Any, Any, Message] | None = None
        """The last reply of the operation."""
    
    def __hash__(self) -> int:
        return self._UID

    def __eq__(self, __obj, /) -> bool:
        if isinstance(__obj, self.__class__):
            return self._UID == __obj._UID
        return NotImplemented
    
    @property
    def Uid(self) -> int:
        """Returns the unique ID of this operation."""
        return self._UID
    
    @property
    def LastReply(self) -> Coroutine[Any, Any, Message] | None:
        """Gets the last reply of the operation."""
        return self._lastReply
    
    def Reply(
            self,
            __coro: Coroutine[Any, Any, Message] | None,
            /,
            *args,
            **kwargs,
            ) -> Coroutine[Any, Any, Message] | None:
        """Saves the last reply and returns it."""
        from functools import partial
        if __coro is None:
            self._lastReply = None
        else:
            self._lastReply = partial(__coro, *args, **kwargs)
        return self.GetLastReply()
    
    def GetLastReply(self) -> Coroutine[Any, Any, Message] | None:
        if self._lastReply is None:
            return None
        else:
            return self._lastReply()
    
    @abstractmethod
    def Start(
            self,
            message: Message
            )  -> WizardRes:
        """Starts this operation."""
        pass

    @abstractmethod
    def ReplyText(
            self,
            message: Message,
            text: str,
            ) -> WizardRes:
        """Optionally replies the provided text. It must return `True` if
        the operation finished otherwise `False`.
        """
        pass

    def ReplyCallback(
            self,
            message: Message,
            cb: str,
            ) -> WizardRes:
        """Optionally replies the provided callback. It must return `True`
        if the operation finished otherwise `False`. Callback data are in the
        format of `<uid>-<cbnum>-<optional>`. The `Uid` must be eliminated
        by operation manager and the rest must be fed into this method.
        """
        pass
