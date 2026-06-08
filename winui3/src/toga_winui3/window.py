from __future__ import annotations

from typing import TYPE_CHECKING

from win32more.Microsoft.UI.Windowing import (
    AppWindowPresenterKind,
    DisplayArea,
    DisplayAreaFallback,
    OverlappedPresenter,
    OverlappedPresenterState,
    TitleBarTheme,
)
from win32more.Microsoft.UI.Xaml import (
    HorizontalAlignment,
    VerticalAlignment,
    WindowActivationState,
)
from win32more.Microsoft.UI.Xaml.Controls import (
    Canvas,
    Grid,
    MenuBar,
    MenuBarItem,
    MenuFlyoutItem,
    MenuFlyoutSeparator,
    MenuFlyoutSubItem,
)
from win32more.Microsoft.UI.Xaml.Media import MicaBackdrop
from win32more.Windows.Graphics import PointInt32, SizeInt32

from toga import App
from toga.command import Separator
from toga.constants import WindowState
from toga.types import Position, Size

from .container import Container
from .libs.misc import column_definition_star, row_definition_auto, row_definition_star
from .screens import Screen as ScreenImpl, round_pixels

if TYPE_CHECKING:  # pragma: no cover
    from toga.types import PositionT, SizeT


class Window:
    def __init__(self, interface, title, position, size):
        self.interface = interface

        self.is_activated = False
        self.create()

        self._set_restrictions()
        self.set_title(title)
        self.set_size(size)

        # Use default behavior for position, rather than Toga's re-implementation.
        if position:
            self.set_position(position)

        # Create the window content and attach it.
        self.create_content()

    def create(self):
        self.native = App.app._impl.native_instance.CreateWindow()
        self.native.SystemBackdrop = MicaBackdrop()
        self.native.AppWindow.TitleBar.PreferredTheme = TitleBarTheme.UseDefaultAppMode

        # TODO: Decide if these event handlers need to be a weak reference.
        self.native.Activated += self.native_event_activated
        self.native.AppWindow.Changed += self.native_event_changed

    def create_content(self):
        """Construct the container."""
        self.container_native = Canvas()
        self.container = Container(self.container_native)
        self.native.Content = self.container_native

    def _set_restrictions(self):
        """Sets the window properties of being minimizable and resizable."""
        presenter = self.native.AppWindow.Presenter
        if presenter.Kind != AppWindowPresenterKind.Overlapped:
            return

        # Cast presenter as an instance of OverlappedPresenter and set the restrictions.
        overlapped_presenter = OverlappedPresenter(value=presenter.value)
        overlapped_presenter.IsMinimizable = self.interface.minimizable
        overlapped_presenter.IsResizable = self.interface.resizable

    ####################################################################################
    # Native event handlers.
    ####################################################################################

    def native_event_activated(self, sender, args):
        """Event that fires when the window is activated or deactivated."""
        # learn.microsoft.com/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.window.activated # noqa: E501
        if args.WindowActivationState == WindowActivationState.Deactivated:
            self.is_activated = False
            self.interface.on_lose_focus()
        else:
            self.is_activated = True
            self.interface.on_gain_focus()

    def native_event_changed(self, sender, args):

        if args.DidPositionChange:
            pass

        if args.DidSizeChange:
            self.interface.on_resize()

        if args.DidVisibilityChange:
            if self.native.AppWindow.IsVisible:
                self.interface.on_show()
            else:
                self.interface.on_hide()

        if args.DidPresenterChange:
            self._set_restrictions()

    ####################################################################################
    # Window properties
    ####################################################################################

    def get_title(self) -> str:
        """Gets the title of the window, i.e. the text on the title bar."""
        return self.native.AppWindow.Title

    def set_title(self, title: str):
        """Sets the title of the window, i.e. the text on the title bar."""
        self.native.AppWindow.Title = title

    ####################################################################################
    # Window lifecycle
    ####################################################################################

    def close(self):
        self.interface.factory.not_implemented("Window.close")
        self.native.Close()

    def set_app(self, app):
        """Sets the window icon to be the icon associated to the given app."""
        self.native.AppWindow.SetIconWithIconId(app.interface.icon._impl.id)

    def show(self):
        if self.interface.content is not None:
            self.interface.content.refresh()

        self.native.AppWindow.Show()

    ####################################################################################
    # Window content and resources.
    ####################################################################################

    def content_refreshed(self, container):
        # TODO: Minimum size constraints: overlapped_presenter.PreferredMinimumWidth.
        self.interface.factory.not_implemented("Window.content_refreshed")

    def set_content(self, widget):
        """Sets the content of the window's container to be the given Toga widget."""
        self.container.content = widget

    ####################################################################################
    # Window size (CSS pixels).
    #
    # Toga terminology <-> Microsoft terminology:
    #   - Physical pixels <-> Device pixels
    #       - The individual physical pixels that comprise the screen.
    #   - CSS pixels <-> Effective pixels
    #       - A virtual unit of measurement used for internal window properties so that
    #         a window appears the on screens with different scale factors.
    #
    # Example: For a 200% scale factor 1 css pixel is a 2x2 block of physical pixels.
    ####################################################################################

    def get_size(self) -> Size:
        """Gets the size of the window in effective pixels (CSS pixels)."""
        # self.native.Bounds returns values in effective pixels, but they are not always
        # integer values.
        return Size(
            round_pixels(self.native.Bounds.Width),
            round_pixels(self.native.Bounds.Height),
        )

    def set_size(self, size: SizeT):
        """Sets the size of the window in effective pixels (CSS pixels)."""
        css_to_physical = self.get_current_screen().css_to_physical

        self.native.AppWindow.Resize(
            SizeInt32(css_to_physical(size[0]), css_to_physical(size[1]))
        )

    ####################################################################################
    # Window position (CSS pixels, see window size for terminology).
    ####################################################################################

    def get_current_screen(self):
        return ScreenImpl(
            DisplayArea.GetFromWindowId(
                self.native.AppWindow.Id,
                DisplayAreaFallback.Primary,
            )
        )

    # Window.position is scaled according to the DPI of the primary screen, because the
    # interface layer assumes that Screen.origin, Window.position and
    # Window.screen_position are all in the same coordinate system.
    #
    # TODO: Remove that assumption, and make Window.position return coordinates relative
    # to the current screen's origin and DPI.
    def get_position(self) -> Position:
        position = self.native.AppWindow.Position
        physical_to_css = App.app._impl.get_primary_screen().physical_to_css

        return Position(physical_to_css(position.X), physical_to_css(position.Y))

    def set_position(self, position: PositionT):
        css_to_physical = App.app._impl.get_primary_screen().css_to_physical

        self.native.AppWindow.Move(
            PointInt32(css_to_physical(position.x), css_to_physical(position.y))
        )

    ####################################################################################
    # Window visibility.
    ####################################################################################

    def get_visible(self) -> bool:
        """Returns True if the window is visible and False otherwise."""
        return self.native.Visible

    def hide(self):
        """Hides but does not destroy the window."""
        self.native.Hide()

    ####################################################################################
    # Window state.
    ####################################################################################

    def get_window_state(self, in_progress_state=False) -> WindowState:
        """Gets the current state of the window.

        :param in_progress_state: Not supported on WinUI 3.
        :return: A WindowState constant determined by NORMAL, MAXIMIZED, MINIMIZED or
            PRESENTATION. FULLSCREEN is not supported.
        """
        presenter = self.native.AppWindow.Presenter

        if presenter.Kind == AppWindowPresenterKind.FullScreen:
            # Fullscreen here corresponds to Toga 'PRESENTATION' window state. From the
            # Microsoft documentation: 'The window does not have a border or title bar,
            # and hides the system task bar.
            # learn.microsoft.com/en-us/windows/apps/develop/ui/manage-app-windows
            return WindowState.PRESENTATION
        else:
            # Assume presenter.Kind == AppWindowPresenterKind.Overlapped, since the
            # third alternative 'CompactOverlay' is not implemented by Toga.
            # learn.microsoft.com/en-us/windows/apps/develop/ui/manage-app-windows
            #
            # Hence, cast presenter as an instance of OverlappedPresenter.
            overlapped_presenter = OverlappedPresenter(value=presenter.value)

            if overlapped_presenter.State == OverlappedPresenterState.Maximized:
                return WindowState.MAXIMIZED
            elif overlapped_presenter.State == OverlappedPresenterState.Minimized:
                return WindowState.MINIMIZED
            else:
                return WindowState.NORMAL

    def set_window_state(self, state: WindowState):
        """Sets the state of the window.

        :state: A WindowState constant determined by NORMAL, MAXIMIZED, MINIMIZED or
            PRESENTATION. FULLSCREEN is not supported and will revert to MAXIMIZED.
        """
        current_state = self.get_window_state()

        if state == current_state:
            return
        elif current_state == WindowState.PRESENTATION:
            self.native.AppWindow.SetPresenter(AppWindowPresenterKind.Overlapped)

        match state:
            case WindowState.PRESENTATION:
                self.native.AppWindow.SetPresenter(AppWindowPresenterKind.FullScreen)

            case WindowState.NORMAL:
                self.native.AppWindow.Presenter.Restore()

            case WindowState.MINIMIZED:
                self.native.AppWindow.Presenter.Minimize()

            case _:
                self.native.AppWindow.Presenter.Maximize()

    ####################################################################################
    # Window capabilities
    ####################################################################################

    def get_image_data(self):
        self.interface.factory.not_implemented("Window.get_image_data")


class MainWindow(Window):
    def create(self):
        super().create()
        self.toolbar_native = None

    def create_content(self):
        # Row 0 is allocated for the menu
        # Row 1 is allocated for toolbar
        self.content_native = Grid()
        self.content_native.ColumnDefinitions.Append(column_definition_star(1))
        self.content_native.RowDefinitions.Append(row_definition_auto())
        self.content_native.RowDefinitions.Append(row_definition_auto())
        self.content_native.RowDefinitions.Append(row_definition_star(1))

        self.content_native.HorizontalAlignment = HorizontalAlignment.Stretch
        self.content_native.VerticalAlignment = VerticalAlignment.Stretch

        self.container_native = Canvas()
        Grid.SetRow(self.container_native, 2)
        Grid.SetColumn(self.container_native, 0)
        self.content_native.Children.Append(self.container_native)

        self.container = Container(self.container_native)

        # Attach the content to the window.
        self.native.Content = self.content_native

    def _submenu(self, group, group_cache):
        try:
            return group_cache[group]
        except KeyError:
            parent_menu = self._submenu(group.parent, group_cache)

            # If group.parent is None, then parent_menu is the MenuBar instance and the
            # type of items that can be added are MenuBarItem. Otherwise, parent_menu is
            # of type MenuBarItem or of type MenuFlyoutSubItem and submenus are added
            # with MenuFlyoutSubItem.
            if group.parent is None:
                submenu = MenuBarItem()
                submenu.Title = group.text
            else:
                submenu = MenuFlyoutSubItem()
                submenu.Text = group.text

            parent_menu.Items.Append(submenu)

            group_cache[group] = submenu
        return submenu

    def create_menus(self):
        self.menu_native = MenuBar()
        self.menu_native.VerticalAlignment = VerticalAlignment.Top
        Grid.SetRow(self.menu_native, 0)
        Grid.SetColumn(self.menu_native, 0)

        group_cache = {None: self.menu_native}

        submenu = None
        for cmd in self.interface.app.commands:
            submenu = self._submenu(cmd.group, group_cache)
            if isinstance(cmd, Separator):
                item = MenuFlyoutSeparator()
            else:
                item = cmd._impl.create_menu_item(MenuFlyoutItem)

            submenu.Items.Append(item)

        self.content_native.Children.Append(self.menu_native)

    def create_toolbar(self):
        if not self.interface.toolbar:
            return

        self.interface.factory.not_implemented("Window.create_toolbars")
