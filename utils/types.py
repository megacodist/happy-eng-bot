#
# 
#
"""This module exposes the specialized types for this Bot:

1. `Strings`
"""

from dataclasses import dataclass


@dataclass
class Language:
    """Represent a language for the GUI."""
    names: dict[str, str]
    messages: dict[str, str]
