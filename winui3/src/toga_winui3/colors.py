from win32more.Microsoft.UI.Xaml.Media import SolidColorBrush
from win32more.Windows.UI import Color as NativeColor

from toga import rgba as TogaColor
from toga.constants import TRANSPARENT

COLOR_CACHE = {}
BRUSH_CACHE = {}


def native_color(toga_color):
    if not toga_color:
        return None

    if toga_color == TRANSPARENT:
        toga_color = TogaColor(0, 0, 0, 0)

    try:
        color = COLOR_CACHE[toga_color]
    except KeyError:
        color = NativeColor()
        color.R = toga_color.rgb.r
        color.G = toga_color.rgb.g
        color.B = toga_color.rgb.b
        color.A = round(toga_color.rgb.a * 255)

        COLOR_CACHE[toga_color] = color

    return color


def native_brush(toga_color):
    color = native_color(toga_color)

    if not color:
        return None

    try:
        brush = BRUSH_CACHE[toga_color]
    except KeyError:
        brush = SolidColorBrush(color)

        BRUSH_CACHE[toga_color] = brush

    return brush
