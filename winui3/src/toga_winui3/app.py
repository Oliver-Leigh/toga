from win32more import String
from win32more.Microsoft.UI.Windowing import DisplayArea
from win32more.Microsoft.UI.Xaml import ApplicationTheme
from win32more.Windows.Win32.Media.Audio import SND_ALIAS, SND_ASYNC, PlaySound
from win32more.Windows.Win32.UI.WindowsAndMessaging import ShowCursor

from .libs.proactor import WinUI3ProactorEventLoop
from .libs.winui3app import WinUI3App
from .screens import Screen as ScreenImpl


class App:
    # Windows applications exit when the last window is closed.
    CLOSE_ON_LAST_WINDOW = True
    # Windows applications use default command line handling.
    HANDLES_COMMAND_LINE = False

    def __init__(self, interface):
        self.interface = interface
        self.interface._impl = self

        # Track whether the app is exiting.
        self._is_exiting = False
        self._exiting_presentation = False

        # The Win32 function ShowCursor is used to show and hide the cursor. Here cursor
        # visibility is represented by a display count. For example, if hide is called N
        # times then to make the cursor re-appear, show must be called N times as well.
        # Hence, a local boolean is stored to avoid a deep stack.
        self._cursor_visible = True

        self.loop = WinUI3ProactorEventLoop()
        self.native_instance: WinUI3App

    def create(self):
        self.native = WinUI3App

        # TODO Ensure that TLS1.2 and TLS1.3 are enabled. See Winforms.

        # Populate the main window as soon as the event loop is running.
        self.loop.call_soon_threadsafe(self.interface._startup)

    ####################################################################################
    # Commands and menus
    ####################################################################################

    def create_standard_commands(self):
        # The standard commands for WinUI 3 are already created by the Toga core
        # interface by calling _create_standard_commands() during _startup().
        pass

    def create_menus(self):
        """Creates menu bars for the windows with the 'create_menus' attribute."""
        for window in self.interface.windows:
            # From toga_winforms:
            # It's difficult to trigger this on a simple window, because we can't easily
            # modify the set of app-level commands that are registered, and a simple
            # window doesn't exist when the app starts up. Therefore, no-branch the else
            # case.
            if hasattr(window._impl, "create_menus"):  # pragma: no branch
                window._impl.create_menus()

    ####################################################################################
    # App lifecycle
    ####################################################################################

    def exit(self):  # pragma: no cover
        # FIXME: App doesn't shutdown correctly with self._is_exiting = True
        self._is_exiting = True
        self.native.Exit(self.native_instance)

    def main_loop(self):
        self.create()
        self.loop.run_forever(self)

    def set_icon(self, icon):
        # Icons are set in Window.set_app().
        pass

    def set_main_window(self, window):
        # Everything is already handled by the Toga core interface.
        pass

    ####################################################################################
    # App resources
    ####################################################################################

    def get_primary_screen(self):
        """Returns the WinUI 3 Screen object for the primary screen."""
        return ScreenImpl(DisplayArea.Primary)

    def get_screens(self):
        """Gets a list of WinUI 3 Screen objects corresponding to the system's screens.

        The primary screen has index 0 within the returned list.
        """
        primary_screen = self.get_primary_screen()
        screen_list = [primary_screen] + [
            ScreenImpl(native=screen)
            for screen in DisplayArea.FindAll()
            if ScreenImpl(native=screen) != primary_screen
        ]
        return screen_list

    ####################################################################################
    # App state
    ####################################################################################

    def get_dark_mode_state(self) -> bool:
        """Returns True if the WinUI3App instance is in dark mode."""
        return self.native_instance.RequestedTheme == ApplicationTheme.Dark

    ####################################################################################
    # App capabilities
    ####################################################################################

    def beep(self):
        """Plays the 'SystemAsterisk' sound."""
        # learn.microsoft.com/windows/win32/multimedia/the-playsound-function
        PlaySound(String("SystemAsterisk"), None, SND_ALIAS | SND_ASYNC)

    def show_about_dialog(self):
        self.interface.factory.not_implemented("App.show_about_dialog")

    ####################################################################################
    # Cursor control
    ####################################################################################

    def hide_cursor(self):
        # learn.microsoft.com/windows/win32/api/winuser/nf-winuser-showcursor
        ShowCursor(False)

    def show_cursor(self):
        # learn.microsoft.com/windows/win32/api/winuser/nf-winuser-showcursor
        ShowCursor(True)

    ####################################################################################
    # Window control
    ####################################################################################

    def get_current_window(self):
        """Returns the currently activated window if one exists, otherwise None."""
        for window in self.interface.windows:
            if window._impl.is_activated:
                return window._impl
        return None

    def set_current_window(self, window):
        """Brings a given window to the foreground and gives it input focus."""
        window._impl.native.Activate()
