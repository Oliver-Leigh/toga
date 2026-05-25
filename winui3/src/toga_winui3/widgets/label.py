from travertino.size import at_least
from win32more.Microsoft.UI.Xaml.Controls import TextBlock

from .base import Widget, WidgetStager


class Label(Widget):
    def create(self):
        self.native = TextBlock()
        self._constraints = WidgetStager(self)
        self._text = ""

    def set_text_align(self, value):
        pass
        # self.native.TextAlign = TextAlignment(value)

    def get_text(self):
        return self.native.Text

    def set_text(self, text):
        self._text = text

        def creator(text=text):
            return text

        self.content_creator = creator

    def rehint(self):
        self.interface.intrinsic.width = at_least(self._constraints.width)
        self.interface.intrinsic.height = self._constraints.height
