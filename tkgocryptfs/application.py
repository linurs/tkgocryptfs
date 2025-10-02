#!/usr/bin/python3
"""
tkgocryptfs is a simple gui for gocryptfs
urs lindegger https://www.linurs.org
"""

import shutil
import argparse

from tkgocryptfs.version import __version__
from tkgocryptfs.tk_application import *

# The root logger
logger = logging.getLogger()


def main() -> None:
    """
    main routine to be called by wrapper scripts
    :return:
    """

    # manage the command line parameters
    # sets default values to variables and modifies their content according the command line parameter passed
    # additionally it handles the -h and --help command line parameter automatically
    parser = argparse.ArgumentParser(
        description='tkgocryptfs - A gui for gocryptfs',
        epilog='urs@linurs.org')
    # command line option to show the programs version
    parser.add_argument('-v', '--version', action='version',
                        # version used in command line option to show the programs version
                        version='%(prog)s ' + __version__)
    # command line option to enable debug messages
    parser.add_argument('-d', '--debug', help="print debug messages", action='store_true')

    # the command line arguments passed
    args = parser.parse_args()

    # Configuring the logger. Levels are DEBUG, INFO, WARNING, ERROR and CRITICAL
    # the parameter filename='example.log' would write it into a file
    logging.basicConfig()  # init logging

    if args.debug:
        logger.setLevel(logging.DEBUG)  # the level producing debug messages
    else:
        logger.setLevel(logging.WARNING)
    logger.debug('Logging debug messages')

    if not shutil.which("gocryptfs"):
        logger.error('gocryptfs not found')

    # start the application
    app = AppT()
    app.run()


if __name__ == "__main__":
    main()
