#
# 
#
"""This module contains the following items:

#### Functions:
1. `PathLikeToPath`
"""


from os import PathLike, fspath
from pathlib import Path


def PathLikeToPath(__pl: PathLike, /) -> Path:
    """Converts a path-like object to a Path object."""
    return __pl if isinstance(__pl, Path) else Path(fspath(__pl))


def SplitOnDash(__str: str, /) -> tuple[str, str]:
    """Splits the dash-delimited argument and returns it as a 2-tuple of
    before-dash part as first element and after-dash part as second element.
    If argument does not contain dash, it returns the whole argument as first
    and an empty string as second element.
    """
    parts = __str.split('-', 1)
    if len(parts) == 1:
        parts.append('')
    return tuple(parts)
