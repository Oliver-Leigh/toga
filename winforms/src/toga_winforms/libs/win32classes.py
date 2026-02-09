from ctypes import (
    POINTER,
    WINFUNCTYPE,
    Structure as c_Structure,
    c_size_t,
)
from ctypes.wintypes import HWND, INT, LPARAM, LPWSTR, UINT, WPARAM



LRESULT = LPARAM  # LPARAM is essentially equivalent to LRESULT
UINT_PTR = c_size_t
DWORD_PTR = c_size_t
PUINT = c_size_t


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-lvitemw
class LVITEMW(c_Structure):
    _fields_ = [
        ("uiMask", UINT),
        ("iItem", INT),
        ("iSubItem", INT),
        ("state", UINT),
        ("stateMask", UINT),
        ("pszText", LPWSTR),
        ("cchTextMax", INT),
        ("iImage", INT),
        ("lParam", LPARAM),
        ("iIndent", INT),
        ("iGroupId", INT),
        ("cColumns", UINT),
        ("puColumns", PUINT),
        ("piColFmt", POINTER(UINT)),
        ("iGroup", INT),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-nmhdr
class NMHDR(c_Structure):
    _fields_ = [
        ("hwndFrom", HWND),
        ("idFrom", UINT_PTR),
        ("code", UINT),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-nmlvdispinfow
class NMLVDISPINFOW(c_Structure):
    _fields_ = [
        ("hdr", NMHDR),
        ("item", LVITEMW),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nc-commctrl-subclassproc
SUBCLASSPROC = WINFUNCTYPE(
    # Return type:
    LRESULT,
    # Argument types:
    HWND,
    UINT,
    WPARAM,
    LPARAM,
    UINT_PTR,
    DWORD_PTR,
)
