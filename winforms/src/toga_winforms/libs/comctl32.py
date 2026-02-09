from ctypes import windll, wintypes

from .win32classes import DWORD_PTR, LRESULT, SUBCLASSPROC, UINT_PTR

comctl32 = windll.comctl32


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-defsubclassproc
DefSubclassProc = comctl32.DefSubclassProc
DefSubclassProc.restype = LRESULT
DefSubclassProc.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass
RemoveWindowSubclass = comctl32.RemoveWindowSubclass
RemoveWindowSubclass.restype = wintypes.BOOL
RemoveWindowSubclass.argtypes = [wintypes.HWND, SUBCLASSPROC, UINT_PTR]


# https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass
SetWindowSubclass = comctl32.SetWindowSubclass
SetWindowSubclass.restype = wintypes.BOOL
SetWindowSubclass.argtypes = [wintypes.HWND, SUBCLASSPROC, UINT_PTR, DWORD_PTR]
