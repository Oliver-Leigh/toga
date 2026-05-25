class StatusIcon:
    pass


class SimpleStatusIcon(StatusIcon):
    pass


class MenuStatusIcon(StatusIcon):
    pass


class StatusIconSet:
    def __init__(self, interface):
        print("Not yet implemented on WinUI3 - StatusIconSet")
        self.interface = interface
        self._menu_items = {}

    def create(self):
        pass
