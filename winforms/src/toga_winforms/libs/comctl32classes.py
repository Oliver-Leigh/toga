from ctypes import Structure as c_Structure
from ctypes.wintypes import DWORD, INT, LPARAM, LPWSTR, RECT, SIZE, UINT

from .win32 import PINT, PUINT

################## comctl32 classes ##################


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
        ("piColFmt", PINT),
        ("iGroup", INT),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-lvcolumnw
class LVCOLUMNW(c_Structure):
    _fields_ = [
        ("mask", UINT),
        ("fmt", INT),
        ("cx", INT),
        ("pszText", LPWSTR),
        ("cchTextMax", INT),
        ("iSubItem", INT),
        ("cchTextMax", INT),
        ("iImage", INT),
        ("iOrder", INT),
        ("cxMin", INT),
        ("cxDefault", INT),
        ("cxIdeal", INT),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-lvtileviewinfo
class LVTILEVIEWINFO(c_Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("dwMask", DWORD),
        ("dwFlags", DWORD),
        ("sizeTile", SIZE),
        ("cLines", INT),
        ("rcLabelMargin", RECT),
    ]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-initcommoncontrolsex
class INITCOMMONCONTROLSEX(c_Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("dwICC", DWORD),
    ]
