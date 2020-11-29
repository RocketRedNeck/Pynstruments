from __future__ import print_function, unicode_literals

import colorama
from colorama import Fore, Back, Style
import sys
from .getch import getch

colorama.init(convert=True)

def pause(message=f'{Fore.BLACK}{Back.WHITE}<ANY KEY TO CONTINUE>{Style.RESET_ALL}'):
    """
    Prints the specified message if it's not None and waits for a keypress.
    """
    if message is not None:
        print(f'{message} {Fore.BLACK}{Back.WHITE}<ANY KEY TO CONTINUE>{Style.RESET_ALL}',end='')
        sys.stdout.flush()
    c = getch() # Modified to return character, which may be useful to some programs
    print('')
    return c


def pause_exit(status=None, message='<ANY KEY TO EXIT>'):
    """
    Prints the specified message if it is not None, waits for a keypress, then
    exits the interpreter by raising SystemExit(status).
    If the status is omitted or None, it defaults to zero (i.e., success).
    If the status is numeric, it will be used as the system exit status.
    If it is another kind of object, it will be printed and the system
    exit status will be 1 (i.e., failure).
    """
    pause(message)
    sys.exit(status)
