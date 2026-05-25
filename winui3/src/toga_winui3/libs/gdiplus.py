from ctypes import WinError, byref

from win32more.Windows.Win32.Foundation import BOOL, UIntPtr
from win32more.Windows.Win32.Graphics.GdiPlus import (
    GdiplusShutdown,
    GdiplusStartup,
    GdiplusStartupInput,
    GdiplusStartupOutput,
)

status_dict = {
    0: "Ok",
    1: "GenericError",
    2: "InvalidParameter",
    3: "OutOfMemory",
    4: "ObjectBusy",
    5: "InsufficientBuffer",
    6: "NotImplemented",
    7: "Win32Error",
    8: "WrongState",
    9: "Aborted",
    10: "FileNotFound",
    11: "ValueOverflow",
    12: "AccessDenied",
    13: "UnknownImageFormat",
    14: "FontFamilyNotFound",
    15: "FontStyleNotFound",
    16: "NotTrueTypeFont",
    17: "UnsupportedGdiplusVersion",
    18: "GdiplusNotInitialized",
    19: "PropertyNotFound",
    20: "PropertyNotSupported",
    21: "ProfileNotFound",
}


class GdiPlus:
    """A context manager for running GdiPlus functions."""

    def __init__(self):
        self._input = GdiplusStartupInput()
        self._input.GdiplusVersion = 1
        self._input.DebugEventCallback = 0
        self._input.SuppressBackgroundThread = BOOL(0)
        self._input.SuppressExternalCodecs = BOOL(0)

        self._token = UIntPtr()
        self._output = GdiplusStartupOutput()

    def __enter__(self):
        status = GdiplusStartup(
            byref(self._token),
            byref(self._input),
            byref(self._output),
        )

        if status != 0:
            raise WinError(
                descr=f"GdiplusStartup failed with code: {status_dict[status]}"
            )

    def __exit__(self, exc_type, exc_value, traceback):
        GdiplusShutdown(self._token)

    def __del__(self):
        pass


gdi_plus = GdiPlus()
