from ctypes.wintypes import SHORT

from win32more.Microsoft.UI.Xaml import GridLength, GridUnitType
from win32more.Microsoft.UI.Xaml.Controls import (
    ColumnDefinition,
    RowDefinition,
)
from win32more.Windows.Win32.Foundation import PWSTR
from win32more.Windows.Win32.UI.WindowsAndMessaging import (
    HICON,
    IMAGE_ICON,
    LR_LOADFROMFILE,
    LoadImageW,
)


def grid_length_auto():
    grid_length = GridLength()
    grid_length.GridUnitType = GridUnitType.Auto

    return grid_length


def grid_length_star(value: int = 1):
    grid_length = GridLength()
    grid_length.GridUnitType = GridUnitType.Star
    grid_length.Value = value

    return grid_length


def column_definition_star(value: int = 1):
    column_definition = ColumnDefinition()
    column_definition.Width = grid_length_star(value)

    return column_definition


def row_definition_auto():
    row_definition = RowDefinition()
    row_definition.Height = grid_length_auto()

    return row_definition


def row_definition_star(value: int = 1):
    row_definition = RowDefinition()
    row_definition.Height = grid_length_star(value)

    return row_definition


# https://learn.microsoft.com/en-us/windows/win32/winmsg/loword
def loword(lparam: int) -> int:
    """Keeps the lower 16 bits of a value with at least 16 bits."""
    return lparam & 0b1111111111111111


# https://learn.microsoft.com/en-us/windows/win32/winmsg/hiword
def hiword(lparam: int) -> int:
    """Keeps the upper 16 bits of value with at least 32 bits."""
    return (lparam >> 16) & 0b1111111111111111


# https://learn.microsoft.com/en-us/windows/win32/api/windowsx/nf-windowsx-get_x_lparam
def get_x_lparam(lparam: int) -> int:
    return SHORT(loword(lparam)).value


# https://learn.microsoft.com/en-us/windows/win32/api/windowsx/nf-windowsx-get_y_lparam
def get_y_lparam(lparam: int) -> int:
    return SHORT(hiword(lparam)).value


def load_icon(path: str) -> HICON:
    """Creates an icon resource from an .ico file."""
    hwnd = LoadImageW(None, PWSTR(path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
    if hwnd is None:
        raise OSError(f"LoadImageW failed to load {path}.")
    return HICON(hwnd)
