from ctypes import byref, c_size_t, c_wchar_p
from ctypes.wintypes import LPARAM, SIZE

from .gdi32 import GetTextExtentPoint32W, SelectObject
from .user32 import GetDC, ReleaseDC, SendMessageW
from .windowconstants import WM_GETFONT

################## functions ##################


# https://learn.microsoft.com/en-us/windows/win32/winmsg/loword
def LOWORD(lparam: int) -> int:
    """Keeps the lower 16 bits of a value with at least 16 bits."""
    return lparam & 0b1111111111111111


# https://learn.microsoft.com/en-us/windows/win32/winmsg/hiword
def HIWORD(lparam: int) -> int:
    """Keeps the upper 16 bits of value with at least 32 bits."""
    return (lparam >> 16) & 0b1111111111111111


def is_submessage(message: int, submessage: int) -> bool:
    """Tests if a message is a bit-wise sub-message of a given message."""
    return (message & submessage) != 0


def str_pixels(text: str, hwnd: int) -> int:
    """Calculates the display width of a string in pixels for a given window."""
    # First retrieve the device context (DC) handle, h_dc, of the ListView. DCs
    # define graphic objects and their attributes.
    # Ref learn.microsoft.com/en-us/windows/win32/gdi/device-contexts
    h_dc = GetDC(hwnd)

    # Then get the handle to the ListView font, h_font, and associate it with the
    # above DC using SelectObject. Note: This replaces h_font with a new object
    # and h_font_old is the previous.
    h_font = SendMessageW(hwnd, WM_GETFONT, 0, 0)
    h_font_old = SelectObject(h_dc, h_font)

    size_receiver = SIZE()
    GetTextExtentPoint32W(h_dc, c_wchar_p(text), len(text), byref(size_receiver))

    # According to the MS documentation h_font should be replaced by h_font_old
    # after it has been used, and the ReleaseDC must be called.
    # Ref learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-selectobject
    #     learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdc
    SelectObject(h_dc, h_font_old)
    ReleaseDC(hwnd, h_dc)

    return size_receiver.cx


################## classes ##################

LONG_PTR = LPARAM
LRESULT = LPARAM  # LPARAM is essentially equivalent to LRESULT
DWORD_PTR = c_size_t
PINT = c_size_t
PUINT = c_size_t
UINT_PTR = c_size_t
