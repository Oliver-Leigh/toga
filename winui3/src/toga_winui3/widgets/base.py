from abc import ABC, abstractmethod
from warnings import warn

from travertino.constants import TRANSPARENT
from travertino.size import at_least
from win32more.Microsoft.UI.Xaml import FocusState
from win32more.Microsoft.UI.Xaml.Controls import Canvas, Control, Panel

from ..colors import native_brush
from ..libs.misc import is_based_on


class WidgetStager:
    def __init__(self, widget):
        self.width = 0
        self.height = 0
        self._widget = widget
        self._widget_copy = None

    def refresh(self):
        self._widget_copy = type(self._widget)(None)
        self._widget_copy.native.SizeChanged += self.native_event_size_changed
        self._widget.container.staging_area.add(self._widget_copy)
        self._widget_copy.native.Content = self._widget.content_creator()

    def native_event_size_changed(self, sender, args):
        self.width = self._widget_copy.native.ActualSize.X
        self.height = self._widget_copy.native.ActualSize.Y

        self._widget.rehint()
        self._widget.container.staging_area.remove(self._widget_copy)
        self._widget_copy = None


class Widget(ABC):
    ####################################################################################
    # Widget creation.
    ####################################################################################

    def __init__(self, interface):
        super().__init__()
        self.interface = interface
        self._container = None
        self._content = None
        self._constraints = None
        self.native = None

        self.create()

    @abstractmethod
    def create(self): ...

    def set_app(self, app):  # noqa B027
        self.interface.factory.not_implemented("Widget.set_app")

    def set_window(self, window):
        self.interface.factory.not_implemented("Widget.set_window")

    ####################################################################################
    # Methods relating to the container.
    ####################################################################################

    @property
    def container(self):
        return self._container

    @container.setter
    def container(self, container):
        if self._container:
            self._container.widgets.remove(self)

        self._container = container
        if container:
            container.widgets.add(self)
            if self._constraints:
                self._constraints.refresh()

        for child in self.interface.children:
            child._impl.container = container

        self.rehint()

    ####################################################################################
    # Methods relating to children.
    ####################################################################################

    def add_child(self, child):
        child.container = self.container

    def insert_child(self, index, child):
        self.add_child(child)

    def remove_child(self, child):
        child.container = None

    ####################################################################################
    # Methods called by the Toga style applicator.
    ####################################################################################

    def set_background_color(self, color):
        cls_native = type(self.native)
        if color is None:
            if is_based_on(cls_native, Control):
                self.native.ClearValue(Control.BackgroundProperty)
            elif is_based_on(cls_native, Panel):
                self.native.Background = native_brush(TRANSPARENT)
            else:
                warn(
                    "Widget.set_background_color(None) has not been configured for the "
                    + f"class {cls_native}.",
                    stacklevel=1,
                )
        else:
            self.native.Background = native_brush(color)

    def set_bounds(self, x, y, width, height):
        self.native.Width = width
        self.native.Height = height
        Canvas.SetLeft(self.native, x)
        Canvas.SetTop(self.native, y)

    def set_color(self, color):
        cls_native = type(self.native)

        # WinUI 3 controls based on the Panel class do not have a Foreground property.
        if is_based_on(cls_native, Panel):
            return

        if color is None:
            if is_based_on(cls_native, Control):
                self.native.ClearValue(Control.ForegroundProperty)
            else:
                warn(
                    "Widget.set_background_color(None) has not been configured for the "
                    + f"class {cls_native}.",
                    stacklevel=1,
                )
        else:
            self.native.Foreground = native_brush(color)

    def set_font(self, font):
        self.interface.factory.not_implemented("Widget.set_font()")

    def set_hidden(self, hidden):
        self.interface.factory.not_implemented("Widget.set_hidden()")

    def set_text_align(self, alignment):
        self.interface.factory.not_implemented("Widget.set_text_align()")

    ####################################################################################
    # Other methods called by the Toga core interface.
    ####################################################################################

    def get_enabled(self):
        return self.native.IsEnabled

    def set_enabled(self, value):
        self.native.IsEnabled = value

    @property
    def has_focus(self):
        return self.native.FocusState != FocusState.Unfocused

    def focus(self):
        self.native.Focus(FocusState.Programmatic)

    def get_tab_index(self):
        return self.native.TabIndex

    def set_tab_index(self, tab_index):
        self.native.TabIndex = tab_index

    def refresh(self):
        self.rehint()

    def rehint(self):
        self.interface.intrinsic.width = at_least(self.interface._MIN_WIDTH)
        self.interface.intrinsic.height = at_least(self.interface._MIN_HEIGHT)

    ####################################################################################
    # Content.
    #
    # These methods are to be used by Widgets that have minimum size constraints based
    # on their content. When these widgets are staged in the container staging area, a
    # copy of the native content needs to be created. It's difficult to created a direct
    # copy of the content, so here a mechanism is used to create a new version of the
    # content using a "content creator".
    ####################################################################################

    @property
    def content_creator(self):
        return self._content_creator

    @content_creator.setter
    def content_creator(self, creator):
        self._content_creator = creator
        self.content = creator()
        self.native.Content = self.content

        if self._container:
            self._constraints.refresh()
