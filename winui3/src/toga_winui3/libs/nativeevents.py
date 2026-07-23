from win32more import ComError

from toga import App
from toga.handlers import WeakrefCallable


class NativeEvent:
    _cleared_callbacks = {}

    def __init__(self, owner, name: str):
        split_name = name.split("_")

        self._owner = owner
        for attribute in split_name[:-1]:
            self._owner = getattr(self._owner, attribute)

        self._name = split_name[-1]
        self._registry = {}

    def __iadd__(self, callback):
        event_adder = getattr(self._owner, "add_" + self._name)

        # Don't allow the external process to keep a reference to the callback.
        token = event_adder(WeakrefCallable(callback))

        # Keep a local reference to the callback.
        self._registry[id(token)] = (token, callback)

        return self

    def clear(self):
        event_remover = getattr(self._owner, "remove_" + self._name)
        for token, callback in self._registry.values():
            try:
                event_remover(token)

            except ComError:
                # This error occurs when the actual WinUI 3 object has been removed, for
                # example when its parent is destroyed, but the python win32more object
                # remains. Since the actual WinUI 3 object has been removed, and hence
                # will not raise any events, this error is ignored.
                pass

            NativeEvent._clear_callback(callback)

        self._registry = {}

    @classmethod
    def _clear_callback(cls, callback):
        # There is potentially still a call to the callback in the message queue
        # after the event has been deregistered. So the task to clear the callback
        # is placed at the back of the queue, and only deletes the
        # reference to the callback after any calls have been made.
        callback_id = id(callback)
        cls._cleared_callbacks[callback_id] = callback

        def clear_callback_task(cls=cls, callback_id=callback_id):
            del cls._cleared_callbacks[callback_id]

        App.app.loop.call_soon_threadsafe(clear_callback_task)


class NativeEventsHandler:
    def __init__(self, owner):
        self._owner = owner
        self._event_registry = {}

    def __getattr__(self, name):
        """Gets the native event for a name with a capital first character."""
        if name not in self._event_registry.keys():
            self._event_registry[name] = NativeEvent(self._owner, name)

        return self._event_registry[name]

    def __setattr__(self, name, value):
        if not name[0].isupper():
            super().__setattr__(name, value)
            return

        self._event_registry[name] = value

    def clear(self):
        for event in self._event_registry.values():
            event.clear()

        self._event_registry = {}


class NativeEventsMixin:
    @property
    def native_class(self):
        return type(self).__bases__[1]

    def __del__(self):
        if getattr(self, "_event_handler", None):
            self.event_handler.clear()

        # This is a safety catch for future changes in the native backend.
        if hasattr(self.native_class, "__del__"):  # pragma: no cover
            super().__del__()

    @property
    def event_handler(self):
        # Lazy load an EventHandler instance.
        if not getattr(self, "_event_handler", None):
            self._event_handler = NativeEventsHandler(self)

        return self._event_handler


def events_handled(native_cls):
    cls_name = native_cls.__name__ + "Handled"
    bases = (NativeEventsMixin, native_cls)
    return type(cls_name, bases, {})()


class EventsHandledMixin:
    @property
    def native_cls(self):
        return self._native_cls if hasattr(self, "_native_cls") else None

    @native_cls.setter
    def native_cls(self, cls):
        self._native_cls = cls
        self.native = events_handled(cls)
