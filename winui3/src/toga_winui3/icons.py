from pathlib import Path

from win32more.Microsoft.UI import IconId
from win32more.Microsoft.UI.Xaml.Controls import ImageIcon
from win32more.Microsoft.UI.Xaml.Media.Imaging import BitmapImage
from win32more.Windows.Foundation import Uri
from win32more.Windows.Win32.UI.WindowsAndMessaging import HICON

########################################################################################
# FIXME: Microsoft.Ui.Interop functionality will be included in a future win32more
# release. Update this code and the flagged code below when that happens.
# https://github.com/ynkdir/py-win32more/issues/184
from winui3.microsoft.ui.interop import get_icon_id_from_icon

########################################################################################
from .libs.gdiplus import create_icon


class Icon:
    EXTENSIONS = [".png", ".bmp"]
    SIZES = None

    def __init__(self, interface, path):
        self.interface = interface
        self._handle: None | HICON = None
        self._id: None | IconId = None
        self._bitmap_image: None | BitmapImage = None

        if path is None:
            self.path = Path(__file__).parent / "resources" / "toga.png"
        else:
            self.path = Path(path)

    @property
    def uri(self) -> Uri:
        return Uri(f"file:///{self.path.as_posix()}")

    @property
    def handle(self) -> HICON:
        """The handle to the Win32 icon object created using the icon's path."""
        if self._handle is None:
            self._handle = create_icon(str(self.path))

        return self._handle

    @property
    def id(self) -> IconId:
        """The IconId to the WinRT icon object created using the icon's path."""
        if self._id is None:
            ################################################################################
            # FIXME: See interop note above.
            icon_id = get_icon_id_from_icon(int(self.handle.value))
            self._id = IconId(icon_id.value)
            ################################################################################

        return self._id

    @property
    def bitmap_image(self) -> BitmapImage:
        """The WinUI 3 BitmapImage used as a source for the icon."""
        if self._bitmap_image is None:
            self._bitmap_image = BitmapImage()
            self._bitmap_image.UriSource = self.uri

        return self._bitmap_image

    @property
    def image_icon(self):
        """The WinUI 3 icon implementation."""
        image_icon = ImageIcon()
        image_icon.Height = 16
        image_icon.Width = 16
        image_icon.Source = self.bitmap_image

        return image_icon
