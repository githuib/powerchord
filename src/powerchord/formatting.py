import os
import sys
from collections.abc import Callable
from functools import cache


@cache
def has_colors() -> bool:
    no = "NO_COLOR" in os.environ
    yes = "CLICOLOR_FORCE" in os.environ
    maybe = sys.stdout.isatty()
    return not no and (yes or maybe)


def _wrap_ansi_code(value: int) -> Callable[[str], str]:
    def wrapper(s: str) -> str:
        return f"\033[{value}m{s}\033[0m" if has_colors() else s

    return wrapper


bright = _wrap_ansi_code(1)
dim = _wrap_ansi_code(2)

black = _wrap_ansi_code(30)
red = _wrap_ansi_code(31)
green = _wrap_ansi_code(32)
yellow = _wrap_ansi_code(33)
blue = _wrap_ansi_code(34)
magenta = _wrap_ansi_code(35)
cyan = _wrap_ansi_code(36)
gray = _wrap_ansi_code(37)

light_gray = _wrap_ansi_code(90)
light_red = _wrap_ansi_code(91)
light_green = _wrap_ansi_code(92)
light_yellow = _wrap_ansi_code(93)
light_blue = _wrap_ansi_code(94)
light_magenta = _wrap_ansi_code(95)
light_cyan = _wrap_ansi_code(96)
white = _wrap_ansi_code(97)

OK = green("✔")
FAIL = red("✘")


def status(success: bool) -> str:
    return OK if success else FAIL


# def status(success: bool) -> Callable[[str], str]:
#     def wrapper(s: str) -> str:
#         return f'{OK if success else FAIL} {s}'
#     return wrapper
#
#
# ok = status(True)
# fail = status(False)
