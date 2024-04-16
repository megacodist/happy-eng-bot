#
# 
#
"""This modules offers utilities to be used for configuring the Bot,
including:

1. `ConfigureLogging`: Configures the logger for saving events to a file.
"""

import logging
from os import PathLike


def ConfigureLogging(filename: PathLike) -> None:
    """Configures the logger for saving events to a file."""
    # Declaring variables ---------------------------------
    import platform
    from datetime import datetime
    # Functionality ---------------------------------------
    # Getting root logger...
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    # Setting two loggers...
    msgOnlyFormatter = logging.Formatter('%(message)s')
    detailedFormatter = logging.Formatter(
        fmt=(
            '[%(asctime)s]  %(module)s  %(threadName)s'
            + '\n%(levelname)8s: %(message)s\n\n'),
        datefmt='%Y-%m-%d  %H:%M:%S')
    fileHandler = logging.FileHandler(filename, 'a')
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(msgOnlyFormatter)
    rootLogger.addHandler(fileHandler)
    # Logging platform information...
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
    fileHandler.setFormatter(detailedFormatter)
    # Setting debugging logger...
    stdoutHandler = logging.StreamHandler()
    stdoutHandler.setFormatter(detailedFormatter)
    stdoutHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(stdoutHandler)
