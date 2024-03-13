#
# 
#
"""This modules offers utilities to be used for configuring the Bot,
including:

1. `ConfigureLogging`: Configures the logger for saving events to a file.
2. `LoadLangs`: Loads `names` and `strings` variables of all installed
languages.
"""

import logging
from os import PathLike

from utils.types import Language


def ConfigureLogging(filename: PathLike) -> None:
    """Configures the logger for saving events to a file."""
    import platform
    from datetime import datetime
    # Getting root logger...
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Logging platform information...
    loggerFileStream = logging.FileHandler(filename, 'a')
    loggerFormatter = logging.Formatter('%(message)s')
    loggerFileStream.setFormatter(loggerFormatter)
    logger.addHandler(loggerFileStream)

    logging.info('=' * 60)
    logNote = (
        f'Operating system: {platform.system()} {platform.release()}'
        + f'(version: {platform.version()}) {platform.architecture()}')
    logging.info(logNote)
    temp = '.'.join(platform.python_version_tuple())
    logNote = f'Python interpreter: {platform.python_implementation()} {temp}'
    logging.info(logNote)
    logging.info(datetime.now().strftime("%A %B %#d, %Y, %H:%M:%S"))
    logging.info('\n\n')

    # Logging program events...
    logger.removeHandler(loggerFileStream)
    loggerFileStream = logging.FileHandler(filename, 'a')
    loggerFormatter = logging.Formatter(
        fmt=(
            '[%(asctime)s]  %(module)s  %(threadName)s'
            + '\n%(levelname)8s: %(message)s\n\n'),
        datefmt='%Y-%m-%d  %H:%M:%S')
    loggerFileStream.setFormatter(loggerFormatter)
    logger.addHandler(loggerFileStream)


def LoadLangs(app_dir: PathLike) -> dict[str, Language]:
    """Loads all installed languages for GUI and returns them all as
    a dictionary. For example to get English language interface,
    use `result['en']`.
    """
    # Declaring variables -----------------------------
    from utils.funcs import PathLikeToPath
    from importlib import import_module
    from types import ModuleType
    langModule: ModuleType
    # Functioning -------------------------------------
    langs: dict[str, Language] = {}
    for file in PathLikeToPath(app_dir / 'langs').glob('*.py'):
        langModule = import_module(f'langs.{file.stem}')
        moduleItems = dir(langModule)
        # Checking existence of 'names' & 'strings'...
        if not set(['names', 'messages']).issubset(set(moduleItems)):
            continue
        # Checking 'names' type...
        langNames = getattr(langModule, 'names')
        if not isinstance(langNames, dict):
            continue
        # Checking 'strings' type...
        langStrings = getattr(langModule, 'messages')
        if not isinstance(langStrings, dict):
            continue
        langs[file.stem] = Language(langNames, langStrings)
    return langs
