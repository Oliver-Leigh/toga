from ctypes import byref
from decimal import ROUND_HALF_EVEN, Decimal

from travertino.size import at_least
from win32more.Windows.Win32.Graphics.Gdi import HMONITOR
from win32more.Windows.Win32.UI.Shell import GetScaleFactorForMonitor
from win32more.Windows.Win32.UI.Shell.Common import DEVICE_SCALE_FACTOR
from winui3.microsoft.ui import DisplayId

# Microsoft.Ui.Interop functionality noy yet included in win32more. So pywinrt is used.
# https://github.com/ynkdir/py-win32more/issues/184
from winui3.microsoft.ui.interop import get_monitor_from_display_id

from toga import App
from toga.screens import Screen as ScreenInterface
from toga.types import Position, Size


def round_pixels(value, rounding=ROUND_HALF_EVEN) -> int:
    if rounding is None:
        return value
    return int(Decimal(value).to_integral(rounding))


class Screen:
    _instances = {}

    def __new__(cls, native):
        native_id = str(native.DisplayId.Value)
        if native_id in cls._instances:
            return cls._instances[native_id]
        else:
            instance = super().__new__(cls)
            instance.interface = ScreenInterface(_impl=instance)
            instance.native = native
            cls._instances[native_id] = instance
            return instance

    def __eq__(self, other) -> bool:
        return self.get_name() == other.get_name()

    @property
    def handle(self) -> HMONITOR:
        return HMONITOR(
            get_monitor_from_display_id(DisplayId(self.native.DisplayId.Value))
        )

    def get_name(self) -> str:
        device_id = str(self.native.DisplayId.Value)
        return "screen-" + device_id

    ####################################################################################
    # DPI scaling
    ####################################################################################

    @property
    def dpi_scale(self) -> float:
        p_scale = DEVICE_SCALE_FACTOR()
        GetScaleFactorForMonitor(self.handle, byref(p_scale))
        return p_scale.value / 100

    def pixels_to_physical(self, value):
        return round_pixels(value * self.dpi_scale)

    def pixels_to_css(self, value):
        if isinstance(value, at_least):
            return at_least(self.pixels_to_css(value.value))
        else:
            return round_pixels(value / self.dpi_scale)

    ####################################################################################
    # Size and position
    ####################################################################################

    # Screen.origin is scaled according to the DPI of the primary screen, because there
    # is no better choice that could cover screens of multiple DPIs.
    def get_origin(self) -> Position:
        native_bounds = self.native.OuterBounds
        pixels_to_css = App.app._impl.get_primary_screen().pixels_to_css

        return Position(pixels_to_css(native_bounds.X), pixels_to_css(native_bounds.Y))

    # Screen.size is scaled according to the screen's own DPI, to be consistent with the
    # scaling of Window size and content.
    def get_size(self) -> Size:
        native_bounds = self.native.OuterBounds
        return Size(
            self.pixels_to_css(native_bounds.Width),
            self.pixels_to_css(native_bounds.Width),
        )

    ####################################################################################
    # Screen capabilities
    ####################################################################################

    def get_image_data(self):
        print("Not yet implemented on WinUI3 - Screen.get_image_data")
