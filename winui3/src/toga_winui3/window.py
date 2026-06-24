from __future__ import annotations

from typing import TYPE_CHECKING

from win32more.Microsoft.UI.Windowing import (
    AppWindowPresenterKind,
    DisplayArea,
    DisplayAreaFallback,
    FullScreenPresenter,
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
from win32more.Windows.Win32.UI.WindowsAndMessaging import (
    MF_BYCOMMAND,
    MF_DISABLED,
    MF_ENABLED,
    MF_GRAYED,
    SC_CLOSE,
    EnableMenuItem,
    GetSystemMenu,
)

########################################################################################
# FIXME: Microsoft.Ui.Interop functionality will be included in a future win32more
# release. Update this code and the flagged code below when that happens.
# https://github.com/ynkdir/py-win32more/issues/184
from winui3.microsoft.ui import WindowId
from winui3.microsoft.ui.interop import get_window_from_window_id

########################################################################################
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

        # From a native WinUI 3 point of view, presentation mode is indistinguishable
        # from fullscreen mode. Use this variable to distinguish between them.
        self._in_presentation_mode = False

        # In WinUI 3 a minimized window is not considered visible. This variable keeps
        # track of this property.
        self._visible = self.native.Visible

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

        # Match the title bar theme to the app.
        self.native.AppWindow.TitleBar.PreferredTheme = TitleBarTheme.UseDefaultAppMode

        # TODO: Decide if these event handlers need to be a weak reference.
        self.native.Activated += self.native_event_activated
        self.native.AppWindow.Changed += self.native_event_changed
        self.native.AppWindow.Closing += self.native_event_closing

    def create_content(self):
        """Construct the container."""
        self.container_native = Canvas()
        self.container = Container(self.container_native, self.content_refreshed)
        self.native.Content = self.container_native

    @property
    def _hwnd(self):
        ################################################################################
        # FIXME: See interop note above.
        window_id = WindowId(self.native.AppWindow.Id.Value)
        return get_window_from_window_id(window_id)
        ################################################################################

    def _set_restrictions(self):
        """Sets the window properties of being minimizable and resizable."""
        presenter, _ = self._presenter

        if presenter.Kind != AppWindowPresenterKind.Overlapped:
            return

        # Set the restrictions.
        presenter.IsMinimizable = self.interface.minimizable
        presenter.IsResizable = self.interface.resizable

        if self.interface.closable:
            self._enable_close_button()
        else:
            self._disable_close_button()

    def _disable_close_button(self):
        # The close button is controlled by the system menu and not the title bar. For
        # an explanation see:
        # https://devblogs.microsoft.com/oldnewthing/20100604-00/?p=13803
        hmenu = GetSystemMenu(self._hwnd, False)
        EnableMenuItem(hmenu, SC_CLOSE, MF_BYCOMMAND | MF_DISABLED | MF_GRAYED)

    def _enable_close_button(self):
        hmenu = GetSystemMenu(self._hwnd, False)
        EnableMenuItem(hmenu, SC_CLOSE, MF_BYCOMMAND | MF_ENABLED)

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
            # Minimize is not considered visible but it also doesn't trigger this event.
            if self.native.AppWindow.IsVisible:
                self._visible = True
                self.interface.on_show()
            else:
                self._visible = False
                self.interface.on_hide()

        if args.DidPresenterChange:
            self._set_restrictions()

    def native_event_closing(self, sender, args):
        # Note: This event is raised when clicking on the close button, but not when
        # self.native.Close() is called.

        if not self.interface.app._impl._is_exiting:
            # In this branch the close request is cancelled and the on_close() method is
            # called. on_close() determines whether a close should occur and then, if
            # appropriate, it will programmatically close the window and remove this
            # handler.
            args.Cancel = True
            self.interface.on_close()

        else:  # pragma: no cover
            # In this branch the app is exiting and the window will close. This can't be
            # triggered in test conditions, so it is as marked no-cover.
            pass

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
        # The native event `Closing` is not called when the Close() method is called
        # programmatically.
        self.native.Close()

    def set_app(self, app):
        """Sets the window icon to be the icon associated to the given app."""
        self.native.AppWindow.SetIconWithIconId(app.interface.icon._impl.id)

    def show(self):
        if self.interface.content is not None:
            self.interface.content.refresh()

        self._visible = True
        self.native.AppWindow.Show()

    ####################################################################################
    # Window content and resources.
    ####################################################################################

    def content_refreshed(self):
        presenter, _ = self._presenter

        if presenter.Kind != AppWindowPresenterKind.Overlapped:
            return

        min_size = self.min_size
        presenter.PreferredMinimumWidth = min_size.width
        presenter.PreferredMinimumHeight = min_size.height

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
        """Gets the size of the window in CSS pixels (effective pixels)."""
        # self.native.Bounds returns values in effective pixels, but they are not always
        # integer values.
        return Size(
            round_pixels(self.native.Bounds.Width),
            round_pixels(self.native.Bounds.Height),
        )

    def set_size(self, size: SizeT):
        """Sets the size of the window in CSS pixels (effective pixels)."""
        css_to_physical = self.get_current_screen().css_to_physical

        self.native.AppWindow.Resize(
            SizeInt32(css_to_physical(size[0]), css_to_physical(size[1]))
        )

    @property
    def min_size(self):
        """The minimum size of the window in physical pixels (device pixels)."""
        css_to_physical = self.get_current_screen().css_to_physical

        # Window and client sizes are in physical pixels.
        window_size = self.native.AppWindow.Size
        client_size = self.native.AppWindow.ClientSize

        # Menu, toolbar and layout values are in CSS pixels.
        menu_native = getattr(self, "menu_native", None)
        menu_height = menu_native.ActualSize.Y if menu_native else 0

        toolbar_native = getattr(self, "toolbar_native", None)
        toolbar_height = toolbar_native.ActualSize.Y if toolbar_native else 0

        layout = self.interface.content.layout

        # Compute the minimum values for the client area.
        client_min_width = css_to_physical(layout.min_width)
        client_min_height = css_to_physical(
            layout.min_height + menu_height + toolbar_height
        )

        return Size(
            window_size.Width - client_size.Width + client_min_width,
            window_size.Height - client_size.Height + client_min_height,
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
    # See: https://github.com/beeware/toga/issues/2947
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
        return self._visible

    def hide(self):
        """Hides but does not destroy the window."""
        self._visible = False
        self.native.Hide()

    ####################################################################################
    # Window state.
    ####################################################################################

    @property
    def _presenter(self):
        raw_presenter = self.native.AppWindow.Presenter

        if raw_presenter.Kind == AppWindowPresenterKind.Overlapped:
            # Cast presenter as an instance of OverlappedPresenter.
            return OverlappedPresenter(value=raw_presenter.value), raw_presenter
        elif raw_presenter.Kind == AppWindowPresenterKind.FullScreen:
            # Cast presenter as an instance of FullScreenPresenter.
            return FullScreenPresenter(value=raw_presenter.value), raw_presenter
        else:
            raise ValueError("CompactOverlay is not a supported presenter type.")

    def get_window_state(self, in_progress_state=False) -> WindowState:
        """Gets the current state of the window.

        :param in_progress_state: Not supported on WinUI 3.
        :return: A WindowState constant determined by NORMAL, MAXIMIZED, MINIMIZED,
            FULLSCREEN or PRESENTATION.
        """
        presenter, _ = self._presenter

        if presenter.Kind == AppWindowPresenterKind.FullScreen:
            # Fullscreen here corresponds to Toga 'PRESENTATION' window state. From the
            # Microsoft documentation: 'The window does not have a border or title bar,
            # and hides the system task bar.'
            # learn.microsoft.com/en-us/windows/apps/develop/ui/manage-app-windows
            if self._in_presentation_mode:
                return WindowState.PRESENTATION
            else:
                return WindowState.FULLSCREEN
        else:
            # Assume presenter.Kind == AppWindowPresenterKind.Overlapped, since the
            # third alternative 'CompactOverlay' is not implemented by Toga.
            if presenter.State == OverlappedPresenterState.Maximized:
                return WindowState.MAXIMIZED
            elif presenter.State == OverlappedPresenterState.Minimized:
                return WindowState.MINIMIZED
            else:
                return WindowState.NORMAL

    def set_window_state(self, state: WindowState):
        """Sets the state of the window.

        :state: A WindowState constant determined by NORMAL, MAXIMIZED, MINIMIZED
            FULLSCREEN or PRESENTATION.
        """
        # If the app is in presentation mode, but this window isn't, then exit app
        # presentation mode before setting the requested state — unless we're
        # entering presentation mode ourselves (to allow multiple windows).
        if state != WindowState.PRESENTATION and any(
            window.state == WindowState.PRESENTATION
            for window in self.interface.app.windows
            if window != self.interface
        ):
            self.interface.app.exit_presentation_mode()

        print("set_window_state")
        from_state = self.get_window_state()
        print(f"from_state:{from_state}")
        if from_state == state:
            return

        from_overlapped = from_state not in {
            WindowState.FULLSCREEN,
            WindowState.PRESENTATION,
        }
        to_overlapped = state not in {WindowState.FULLSCREEN, WindowState.PRESENTATION}

        if from_overlapped and not to_overlapped:
            # Change from overlapped presenter to fullscreen presenter.
            self.native.AppWindow.SetPresenterByKind(AppWindowPresenterKind.FullScreen)

        elif not from_overlapped and to_overlapped:
            # Change from fullscreen presenter to overlapped presenter.
            self.native.AppWindow.SetPresenterByKind(AppWindowPresenterKind.Overlapped)

        if state == WindowState.PRESENTATION:
            self._in_presentation_mode = True
            if hasattr(self, "menu_native"):
                self.menu_native.Visible = False

            if hasattr(self, "toolbar_native"):
                self.toolbar_native.Visible = False

            return

        self._in_presentation_mode = False
        if hasattr(self, "menu_native"):
            self.menu_native.Visible = True

        if hasattr(self, "toolbar_native"):
            self.toolbar_native.Visible = True

        match state:
            case WindowState.NORMAL:
                presenter, _ = self._presenter
                presenter.Restore()

            case WindowState.MINIMIZED:
                presenter, _ = self._presenter
                presenter.Minimize()

            case WindowState.MAXIMIZED:
                presenter, _ = self._presenter
                presenter.Maximize()

            case _:
                # WindowState.FULLSCREEN
                pass

    ####################################################################################
    # Window capabilities
    ####################################################################################

    def get_image_data(self):
        self.interface.factory.not_implemented("Window.get_image_data")
        # Windows.Graphics.Capture


class MainWindow(Window):
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

        self.container = Container(self.container_native, self.content_refreshed)

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
