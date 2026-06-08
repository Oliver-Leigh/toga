from ctypes import POINTER, WinError, byref

from win32more import String
from win32more.Windows.Win32.Foundation import BOOL, UIntPtr
from win32more.Windows.Win32.Graphics.GdiPlus import (
    FontStyleBold,
    FontStyleBoldItalic,
    FontStyleItalic,
    # GDI+ Fonts
    FontStyleRegular,
    FontStyleStrikeout,
    FontStyleUnderline,
    # GDI+ Icons
    GdipCreateBitmapFromFile,
    GdipCreateFontFamilyFromName,
    GdipCreateHICONFromBitmap,
    GdipIsStyleAvailable,
    # Main GDI+ operations
    GdiplusShutdown,
    GdiplusStartup,
    GdiplusStartupInput,
    GdiplusStartupOutput,
    GpBitmap,
    GpFontFamily,
)
from win32more.Windows.Win32.UI.WindowsAndMessaging import HICON

########################################################################################
# Main GDI+ operations
########################################################################################

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


class GdiPlusContext:
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


gdi_plus_context = GdiPlusContext()


########################################################################################
# GDI+ fonts
########################################################################################

FontFamilyPtr = POINTER(GpFontFamily)


ALL_FONT_STYLES = (
    FontStyleRegular
    | FontStyleBold
    | FontStyleItalic
    | FontStyleBoldItalic
    | FontStyleUnderline
    | FontStyleStrikeout
)


def is_font_installed(font_family_name: str):
    """Checks whether a font is installed on the current system.

    Note that the font family name must be exactly as it appears in the Windows Settings
    under Personalization > Fonts.

    For example, "Times New Roman" will load but variations such as "Times New", "Times
    New Roman Bold" will not.
    """
    with gdi_plus_context:
        font_family_ptr = FontFamilyPtr()
        font_available = BOOL()

        # Attempt to create the font family.
        GdipCreateFontFamilyFromName(
            String(font_family_name), None, byref(font_family_ptr)
        )

        # Check if the font family has been created.
        GdipIsStyleAvailable(font_family_ptr, ALL_FONT_STYLES, byref(font_available))

    return font_available.value == 1


########################################################################################
# GDI+ icons
########################################################################################

BitmapPtr = POINTER(GpBitmap)


def create_icon(icon_path: str) -> HICON:
    """Creates a Win32 icon from a file."""
    bitmap_ptr = BitmapPtr()
    icon_handle = HICON()

    bitmap_status = 1
    handle_status = 1
    with gdi_plus_context:
        bitmap_status = GdipCreateBitmapFromFile(String(icon_path), byref(bitmap_ptr))
        handle_status = GdipCreateHICONFromBitmap(bitmap_ptr, byref(icon_handle))

    if bitmap_status != 0 or handle_status != 0:
        message = f"Unable to create icon bitmap from {icon_path}.\n"
        if bitmap_status != 0:
            message += "GdipCreateBitmapFromFile code: "
            message += str(status_dict[bitmap_status])
        else:
            message += "GdipCreateHICONFromBitmap code: "
            message += str(status_dict[handle_status])

        raise ValueError(message)

    return icon_handle
