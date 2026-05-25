from ctypes import POINTER, byref
from pathlib import Path

from win32more import String
from win32more.Microsoft.UI import IconId
from win32more.Microsoft.UI.Xaml.Controls import BitmapIcon
from win32more.Windows.Foundation import Uri
from win32more.Windows.Win32.Graphics.GdiPlus import (
    GdipCreateBitmapFromFile,
    GdipCreateHICONFromBitmap,
    GpBitmap,
)
from win32more.Windows.Win32.UI.WindowsAndMessaging import HICON

# Use pywinrt is until Microsoft.Ui.Interop is included in a release of win32more:
# https://github.com/ynkdir/py-win32more/issues/184
from winui3.microsoft.ui.interop import get_icon_id_from_icon

from .libs.gdiplus import gdi_plus, status_dict

BitmapPtr = POINTER(GpBitmap)


class Icon:
    EXTENSIONS = [".png", ".bmp"]
    SIZES = None

    def __init__(self, interface, path):
        self.interface = interface
        self._handle: None | HICON = None
        self._id: None | IconId = None
        self._bitmap_icon: None | BitmapIcon = None

        if path is None:
            self.path = Path(__file__).parent / "resources" / "toga.png"
        else:
            self.path = Path(path)

    @property
    def uri(self) -> Uri:
        return Uri(f"ms-appx:///{self.path.as_posix()}")

    @property
    def handle(self) -> HICON:
        """The handle to the Win32 icon object created using the icon's path."""
        if self._handle is None:
            bitmap_ptr = BitmapPtr()
            self._handle = HICON()

            bitmap_status = 1
            handle_status = 1
            with gdi_plus:
                bitmap_status = GdipCreateBitmapFromFile(
                    String(str(self.path)), byref(bitmap_ptr)
                )
                handle_status = GdipCreateHICONFromBitmap(
                    bitmap_ptr, byref(self._handle)
                )

            if bitmap_status != 0 or handle_status != 0:
                message = f"Unable to create icon bitmap from {self.path}.\n"
                if bitmap_status != 0:
                    message += "GdipCreateBitmapFromFile code: "
                    message += str(status_dict[bitmap_status])
                else:
                    message += "GdipCreateHICONFromBitmap code: "
                    message += str(status_dict[handle_status])

                raise ValueError(message)

        return self._handle

    @property
    def id(self) -> IconId:
        """The IconId to the WinRT icon object created using the icon's path."""
        if self._id is None:
            icon_id = get_icon_id_from_icon(int(self.handle.value))
            self._id = IconId(icon_id.value)

        return self._id

    @property
    def bitmap_icon(self) -> BitmapIcon:
        # FIXME: NOT WORKING
        if self._bitmap_icon is None:
            self._bitmap_icon = BitmapIcon()
            self._bitmap_icon.UriSource = self.uri
        return self._bitmap_icon
