"""
static functions
"""
import re
from tkinter import messagebox
from tkgocryptfs.version import __version__


def about() -> None:
    """
    Show the about window
    """
    messagebox.showinfo("About",
                        "tkgocryptfs a gui front end for gocryptfs from https://www.linurs.org \nVersion " + __version__)


def remove_esc(s: str) -> str:
    """
    remove escape string from terminal output so it does not appear in the gui windows
    :param s: input string
    :return: cleaned string
    """
    clean_1 = re.sub(r'\x1B\[[0-9;]*[A-Za-z]', '', s)
    clean_2 = clean_1.replace("\r\n", "\n")
    return clean_2
