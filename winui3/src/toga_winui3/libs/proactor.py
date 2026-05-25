import asyncio
import sys
import threading
import traceback
from asyncio import events
from functools import partial

from win32more.Microsoft.UI.Dispatching import DispatcherQueue, DispatcherQueueTimer
from win32more.Windows.Foundation import TimeSpan

# TODO: This is largely copied from WinformsProactorEventLoop which has the same 5ms
# polling delay. Remove this delay in a future version.

# FIXME: Loop doesn't shut down correctly.


def native_app_launched(loop, winui3_app, args):
    """A function to be used as an override of the OnLauched method of WinUI3App."""
    asyncio.set_event_loop(loop)
    loop.dispatcher = DispatcherQueue.GetForCurrentThread()
    loop.queue_timer = loop.dispatcher.CreateTimer()
    loop.queue_timer.IsRepeating = False
    loop.queue_timer.Tick += loop.tick

    loop.app.native_instance = winui3_app

    loop.enqueue_tick()


# Can't get coverage for app shutdown, so this handler must be no-cover.
def native_app_exited(loop, winui3_app):  # pragma: no cover
    """Perform cleanup that needs to occur when the app exits.

    This largely duplicates the "finally" behavior of the default Proactor
    run_forever implementation.
    """
    if sys.version_info < (3, 13):
        # If we're stopping, we can do the "finally" handling from
        # the BaseEventLoop run_forever(). In Python 3.13.0a2, this
        # was refactored into the `_run_forever_cleanup()` helper.
        # We run testbed on Py3.12, so the else branch is marked
        # nocover.
        # === START BaseEventLoop.run_forever() finally handling ===
        loop._stopping = False
        loop._thread_id = None
        events._set_running_loop(None)
        loop._set_coroutine_origin_tracking(False)
        sys.set_asyncgen_hooks(*loop._old_agen_hooks)
        # === END BaseEventLoop.run_forever() finally handling ===
    else:  # pragma: no cover
        loop._run_forever_cleanup()


class WinUI3ProactorEventLoop(asyncio.ProactorEventLoop):
    def run_forever(self, app):
        """Set up the asyncio event loop, integrate it with the native event loop, and
        start the application.

        This largely duplicates the setup behavior of the default Proactor
        run_forever implementation.

        :param app_context: The WinForms.ApplicationContext instance
            controlling the lifecycle of the app.
        """
        # Python 3.8 added an implementation of run_forever() in
        # ProactorEventLoop. The only part that actually matters is the
        # refactoring that moved the initial call to stage _loop_self_reading;
        # it now needs to be created as part of run_forever; otherwise the
        # event loop locks up, because there won't be anything for the
        # select call to process.
        self.call_soon(self._loop_self_reading)

        # Remember the application.
        self.app = app

        # Set up the Proactor.
        if sys.version_info < (3, 13):
            # The code between the following markers should be exactly the same
            # as the official CPython implementation, up to the start of the
            # `while True:` part of run_forever() (see
            # BaseEventLoop.run_forever() in Lib/ascynio/base_events.py). In
            # Python 3.13.0a2, this was refactored into the
            # `_run_forever_setup()` helper. We run testbed on Py3.10, so the
            # else branch is marked nocover.
            # === START BaseEventLoop.run_forever() setup ===
            self._check_closed()
            if self.is_running():  # pragma: no cover
                raise RuntimeError("This event loop is already running")
            if events._get_running_loop() is not None:  # pragma: no cover
                raise RuntimeError(
                    "Cannot run the event loop while another loop is running"
                )
            self._thread_id = threading.get_ident()
            self._old_agen_hooks = sys.get_asyncgen_hooks()
            sys.set_asyncgen_hooks(
                firstiter=self._asyncgen_firstiter_hook,
                finalizer=self._asyncgen_finalizer_hook,
            )

            events._set_running_loop(self)
            # === END BaseEventLoop.run_forever() setup ===
        else:  # pragma: no cover
            self._orig_state = self._run_forever_setup()

        # Rather than going into a `while True:` loop, we're going to use the
        # native event loop to queue a tick() message that will cause a
        # single iteration of the asyncio event loop to be executed. Each time
        # we do this, we queue *another* tick() message in 5ms time. In this
        # way, we'll get a continuous stream of tick() calls, without blocking
        # the native event loop. We also add a handler for ApplicationExit
        # to ensure that loop cleanup occurs when the app exits.

        self.dispatcher: DispatcherQueue
        self.queue_timer: DispatcherQueueTimer
        self._inner_loop = None

        app.native.OnLaunched = partial(native_app_launched, self)
        app.native.OnExited = partial(native_app_exited, self)

        # Start the native event loop.
        app.native.Start()

    def enqueue_tick(self, delay=5):
        # Queue a call to tick in a specified delay.
        # TimeSpan is given in 100-nanosecond units i.e. 1E-7.
        self.queue_timer.Interval = TimeSpan(delay * 10000)
        self.queue_timer.Start()

    # This function doesn't report as covered because it runs on a
    # non-Python-created thread (see App.run_app). But it must actually be
    # covered, otherwise nothing would work.
    def tick(self, *args, **kwargs):  # pragma: no cover
        """Cause a single iteration of the event loop to run on the main GUI thread."""
        # FIXME: For some reason the queue timer doesn't work properly when the
        # following line is removed.
        self.queue_timer.IsRunning  # noqa: B018
        self.run_once_recurring()

    # Call native thread blocking methods via this method to ensure the inner loop is
    # correctly linked with this Python loop.
    def start_inner_loop(self, callback, *args):
        assert self._inner_loop is None
        self._inner_loop = (callback, args)

    def run_once_recurring(self):
        """Run one iteration of the event loop, and enqueue the next iteration (if we're
        not stopping).
        """
        try:
            # If the app is exiting, stop the asyncio event loop.
            # Otherwise, perform one more tick of the event loop.
            # We can't get coverage of app shutdown, so that branch
            # is marked no cover
            if self.app._is_exiting:
                self.stop()  # pragma: no cover
            else:
                self._run_once()

            # Enqueue the next tick, and make sure there will be *something*
            # to be processed. If you don't ensure there is at least one
            # message on the queue, the select() call will block, locking
            # the app.  Determine the delay of the tick by checking if
            # there are events that can be processed sooner than 5ms, as
            # we do not want to hold them back from being processed.
            if self._ready:
                delay = 0
            elif self._scheduled:
                first = self._scheduled[0]
                ms_until = int(max(0, (first.when() - self.time()) * 1000))
                delay = min(5, ms_until)
            else:
                delay = 5
            self.enqueue_tick(delay=delay)
            self.call_soon(self._loop_self_reading)

            if self._inner_loop:
                callback, args = self._inner_loop
                self._inner_loop = None
                callback(*args)

        # Exceptions thrown by this method will be silently ignored.
        except BaseException:  # pragma: no cover
            traceback.print_exc()
