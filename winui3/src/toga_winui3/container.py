from math import ceil

from win32more.Microsoft.UI.Xaml import HorizontalAlignment, VerticalAlignment
from win32more.Microsoft.UI.Xaml.Controls import Canvas, RelativePanel


class ContainerWidgets:
    """A class used to add, remove and keep a record of the Container's widgets."""

    def __init__(self, container):
        self._container = container
        self._widgets = []

    @property
    def _native(self):
        return self._container.native

    def clear(self):
        if len(self._widgets) < 1:
            return

        for widget in self._widgets:
            widget.container = None
            self._widgets = []

        self._native.Children.Clear()

    def add(self, widget):
        self._widgets.append(widget)
        self._native.Children.Append(widget.native)

    def remove(self, widget):
        index = self._widgets.index(widget)
        self._widgets.remove(widget)
        self._native.Children.RemoveAt(index)


class ContainerStagingArea(ContainerWidgets):
    """A class used to calculate content-based constraints for WinUI 3 widgets.

    Some WinUI 3 widgets such as Button require minimum size constraints that are only
    be calculated once they are attached to a window. ContainerStagingArea uses a hidden
    panel (self._native) which allows the widgets to resize based on native parameters.

    This class should be use in conjunction with WidgetStager
    """

    @property
    def _native(self):
        return self._container._staging_panel

    def remove(self, widget):
        """Removes a widget and triggers a layout refresh when the widget list empties.

        The refresh mechanism here is to avoid excessive refreshes. A single refresh
        call will cause every widget in the Container to be refreshed. For example if a
        Container had 100 buttons attached, then each button would be refreshed 100
        times with 10,000 total refresh calls (compared with the ~1 refresh call here).
        """
        non_empty_initial = len(self._widgets) > 0
        super().remove(widget)
        empty_final = len(self._widgets) == 0

        if non_empty_initial and empty_final:
            if self._container._content:
                self._container._content.interface.refresh()


class Container:
    """A container used for laying out WinUI 3 Toga widgets.

    A Container represents a region of window where the dimensions are controlled by
    the native runtime. It primarily does:
        - Reports the dimensions of the region to the Toga core interface.
        - Notifies the Toga core interface when the dimensions change.
        - Provides a native panel where the widgets.native classes can be attached.

    The actual layout of the widgets attached to a Container is determined by the style
    applicator of the Toga core interface.

    Attributes:
        native: The WinUI 3 panel where the widgets.native classes will be attached.
        widgets: A ContainerWidgets instance which adds, removes and keeps a record of
            the widgets attached to the native panel.
        staging_area: A ContainerStagingArea instance which is used to stage widgets
            that require a native panel to calculate content-based constraints.
    """

    def __init__(self, native_panel: Canvas):
        """Initialize a Container using a given native panel.

        :param container_native: The native panel where the widgets.native classes can
            be attached.
        """
        self.native = native_panel
        self.native.HorizontalAlignment = HorizontalAlignment.Stretch
        self.native.VerticalAlignment = VerticalAlignment.Stretch
        self.native.SizeChanged += self.native_event_size_changed

        self._content = None
        self.widgets = ContainerWidgets(self)

        self._staging_panel = RelativePanel()
        self._staging_panel.Visible = False
        self.native.Children.Append(self._staging_panel)

        self.staging_area = ContainerStagingArea(self)

    ####################################################################################
    # Container geometry
    #
    # Note: WinUI 3 sizes are given in CSS pixels and can be factional valued. However,
    #       the Toga core interface uses whole CSS pixels for layouts. When the native
    #       values are rounded down noticeable bars appear at the right side and bottom
    #       of the container during resize. Rounding up causing the content to overlap
    #       with the edge and the bars disappear. This is judged to be the lesser of two
    #       evils.
    ####################################################################################

    @property
    def width(self):
        return ceil(self.native.ActualSize.X)

    @property
    def height(self):
        return ceil(self.native.ActualSize.Y)

    ####################################################################################
    # Container content
    ####################################################################################

    @property
    def content(self):
        """The root widget for the tree of widgets laid out by the container.

        All children of the root widget will also be added to the container as a result
        of assigning content.

        If the container already has content, the old content will be replaced. The old
        root widget and all its children will be removed from the container.
        """
        return self._content

    @content.setter
    def content(self, widget):
        if self._content:
            self._content.container = None

        self._content = widget
        if widget:
            widget.container = self

    ####################################################################################
    # Container refreshing
    ####################################################################################

    def native_event_size_changed(self, sender, args):
        if self.content is not None:
            self.content.interface.refresh()

    def refreshed(self):
        pass
