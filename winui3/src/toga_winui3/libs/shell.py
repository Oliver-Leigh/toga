from ctypes import POINTER, windll
import ctypes.wintypes as wt

from . import win32structures as ws

shell32 = windll.shell32


# https://learn.microsoft.com/windows/win32/api/shellapi/nf-shellapi-shell_notifyiconw
Shell_NotifyIconW = shell32.Shell_NotifyIconW
Shell_NotifyIconW.restype = wt.BOOL
Shell_NotifyIconW.argtypes = [wt.DWORD, POINTER(ws.NOTIFYICONDATAW)]
