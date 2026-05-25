from win32more.Microsoft.UI.Xaml.Controls import Canvas

from .base import Widget


class Box(Widget):
    def create(self):
        self.native = Canvas()
