from ctypes import byref, sizeof, windll
from typing import Literal
import asyncio

from toga import Size

from win32more.Microsoft.UI.Interop import GetWindowFromWindowId
from win32more.Microsoft.UI.Windowing import (
    AppWindowPresenterKind,
    OverlappedPresenterState,
)
from win32more.Microsoft.UI.Xaml import Window as NativeWindow
from win32more.Windows.Win32.UI.WindowsAndMessaging import (
    SetForegroundWindow,
    TITLEBARINFOEX, 
    WM_GETTITLEBARINFOEX
)


from .probe import BaseProbe


class WindowProbe(BaseProbe):
    supports_closable = False # FIXME: Use Win32
    supports_minimizable = True
    supports_move_while_hidden = True
    supports_unminimize = True
    supports_minimize = True
    supports_placement = True
    supports_as_image = True
    supports_focus = True
    fullscreen_presentation_equal_size = True
    maximize_fullscreen_presentation_equal_size = False

    def __init__(self, app, window):
        self.app = app
        self.window = window
        self.impl = window._impl
        super().__init__(window._impl.native)
        assert isinstance(self.native, NativeWindow)

    @property
    def _hwnd(self):
        return GetWindowFromWindowId(self.impl.native.AppWindow.Id)

    async def wait_for_window(
        self,
        message,
        state=None,
    ):
        await self.redraw(message)

        if state:
            timeout = 5
            polling_interval = 0.1
            exception = None
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            while (loop.time() - start_time) < timeout:
                try:
                    assert self.instantaneous_state == state
                    return
                except AssertionError as e:
                    exception = e
                    await asyncio.sleep(polling_interval)
                    continue
                raise exception
            
    @property
    def instantaneous_state(self):
        return self.impl.get_window_state(in_progress_state=False)
