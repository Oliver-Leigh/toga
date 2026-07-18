from travertino.constants import CENTER, JUSTIFY, LEFT, RIGHT
from travertino.size import at_least
from win32more.Microsoft.UI.Xaml import (
    FocusState,
    HorizontalAlignment,
    TextAlignment,
    VerticalAlignment,
)
from win32more.Microsoft.UI.Xaml.Controls import Grid, TextBlock

from ..colors import native_brush
from ..libs.misc import column_definition_star, row_definition_auto
from ..libs.nativeevents import EventsHandledMixin
from .base import Widget
from .properties.native import NativeProperties
from .properties.staged import StagedProperties


class LabelText(EventsHandledMixin):
    def __init__(self, label):
        self._label = label

        self.native_cls = TextBlock

        self._native_properties = NativeProperties(self)
        self._staged_properties = StagedProperties(self)

        Grid.SetRow(self.native, 0)
        Grid.SetColumn(self.native, 0)
        label.native.Children.Append(self.native)

        self.native.HorizontalAlignment = HorizontalAlignment.Stretch
        self.native.VerticalAlignment = VerticalAlignment.Stretch

    @property
    def container(self):
        return self._label.container

    @property
    def _min_width(self):
        return self._label._min_width

    @_min_width.setter
    def _min_width(self, value):
        self._label._min_width = value

    @property
    def _min_height(self):
        return self._label._min_height

    @_min_height.setter
    def _min_height(self, value):
        self._label._min_height = value

    def rehint(self):
        self._label.rehint()


class Label(Widget):
    def create(self):
        self.native_cls = Grid

        self._background_properties = self._native_properties

        self.native.ColumnDefinitions.Append(column_definition_star(1))
        self.native.RowDefinitions.Append(row_definition_auto())

        self.label_text = LabelText(self)
        self._native_properties = self.label_text._native_properties
        self._staged_properties = self.label_text._staged_properties

        self._text = ""

        # Initial minimum sizes are 0 so that the staged properties are sized up.
        self._min_width = 0
        self._min_height = 0

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
        self._background_properties.Background = native_brush(color)

    def set_text_align(self, alignment):
        property_dict = {
            CENTER: "Center",
            JUSTIFY: "Justify",
            LEFT: "Left",
            RIGHT: "Right",
        }
        property = property_dict[alignment]
        native_alignment = getattr(TextAlignment, property)

        self._native_properties.TextAlignment = native_alignment

    ####################################################################################
    # Overrides of other methods called by the Toga core interface.
    ####################################################################################

    def get_enabled(self):
        # Neither TextBlock or Grid has the IsEnabled property.
        return True

    def set_enabled(self, value):
        # Neither TextBlock or Grid has the IsEnabled property.
        pass

    @property
    def has_focus(self):
        grid_has_focus = self.native.FocusState != FocusState.Unfocused
        text_has_focus = self.label_text.native.FocusState != FocusState.Unfocused
        return grid_has_focus or text_has_focus

    def focus(self):
        self.label_text.native.Focus(FocusState.Programmatic)

    def get_tab_index(self):
        return self.label_text.native.TabIndex

    def set_tab_index(self, tab_index):
        self.label_text.native.TabIndex = tab_index

    def rehint(self):
        self.interface.intrinsic.width = at_least(self._min_width)
        self.interface.intrinsic.height = self._min_height
