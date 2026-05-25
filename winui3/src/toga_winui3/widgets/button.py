from travertino.size import at_least
from win32more.Microsoft.UI.Xaml.Controls import (
    Button as NativeButton,
    Symbol,
    SymbolIcon,
)

from .base import Widget, WidgetStager


class Button(Widget):
    def create(self):
        self.native = NativeButton()
        self._constraints = WidgetStager(self)
        self._icon = None
        self._text = ""

        self.native.Click += self.native_event_click

    def native_event_click(self, sender, args):
        self.interface.on_press()

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text

        if self._icon is not None:
            return

        def creator(text=text):
            # "\u200b" (ZERO WIDTH SPACE) instead of "" ensures correct button height.
            return "\u200b" if text == "" else text

        self.content_creator = creator

    def get_icon(self):
        return self._icon

    def set_icon(self, icon):
        self._icon = icon

        if icon is None:
            return

        def creator():
            symbol_icon = SymbolIcon()
            symbol_icon.Symbol = Symbol.Document
            return symbol_icon

        self.content_creator = creator

    def rehint(self):
        self.interface.intrinsic.width = at_least(self._constraints.width)
        self.interface.intrinsic.height = self._constraints.height
