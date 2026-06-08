from travertino.constants import CENTER, JUSTIFY, LEFT, RIGHT
from travertino.size import at_least
from win32more.Microsoft.UI.Xaml import TextAlignment
from win32more.Microsoft.UI.Xaml.Controls import TextBlock

from .base import Widget


class Label(Widget):
    def create(self):
        self.native = TextBlock()
        self._text = ""

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text
        self._staged_properties.Text = self.text

    def text(self):
        return self._text

    ####################################################################################
    # Overrides of methods called by the Toga style applicator.
    ####################################################################################

    def set_background_color(self, color):
        # TextBlock has no Background attribute to set.
        pass

    def set_text_align(self, alignment):
        property_dict = {
            CENTER: "Center",
            JUSTIFY: "Justify",
            LEFT: "Left",
            RIGHT: "Right",
        }
        property = property_dict[alignment]
        native_alignment = getattr(TextAlignment, property)

        self._native_properties.HorizontalTextAlignment = native_alignment

    ####################################################################################
    # Overrides of other methods called by the Toga core interface.
    ####################################################################################

    def rehint(self):
        self.interface.intrinsic.width = at_least(self._min_width)
        self.interface.intrinsic.height = self._min_height
