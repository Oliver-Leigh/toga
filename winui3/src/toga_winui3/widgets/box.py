from win32more.Microsoft.UI.Xaml.Controls import Canvas

from .base import Widget


class Box(Widget):
    def create(self):
        self.native = Canvas()

    ####################################################################################
    # Overrides of methods called by the Toga style applicator.
    ####################################################################################

    def set_color(self, font):
        # Canvas has no Foreground attributes to set.
        pass

    def set_font(self, font):
        # Canvas has no font attributes to set.
        pass
