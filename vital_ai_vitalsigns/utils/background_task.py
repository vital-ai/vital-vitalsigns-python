"""One correct implementation of the periodic background-task lifecycle.

VitalSigns and VitalService each hand-rolled this pattern, and the copies drifted:
a fix applied to one left the identical bugs live in the other. The bugs this
mixin exists to prevent, all of which shipped in at least one copy:

  - an unguarded loop body, so a single exception killed the thread silently and
    permanently -- taking the periodic work with it for the process lifetime
  - a coarse `time.sleep(interval)`, so stop() blocked for up to a full interval
    per instance
  - `if not running: running = True; spawn`, a check-then-act race that let
    concurrent callers each spawn a thread, with all but the last orphaned and
    unreachable
  - `join()` with no timeout, so one wedged thread hung shutdown forever

Subclasses implement `_background_tick()` and may override the interval class
attributes.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class BackgroundTaskMixin:

    # seconds between ticks
    BG_INTERVAL_SECONDS = 60

    # granularity of the loop's sleep, so stop() returns promptly rather than
    # blocking for a whole interval
    BG_SLEEP_SLICE_SECONDS = 1

    # how long stop() waits for the thread before giving up on the join
    BG_JOIN_TIMEOUT_SECONDS = 30

    def _init_background_task(self):
        """Initialize lifecycle state. Call from the subclass __init__."""
        self._bg_running = False
        self._bg_thread = None
        self._lifecycle_lock = threading.RLock()

    def _background_tick(self):
        """One unit of periodic work. Subclasses override."""
        raise NotImplementedError

    def _background_task_name(self):
        return type(self).__name__

    def background_task(self):
        while self._bg_running:
            try:
                self._background_tick()
            except Exception as e:
                # Never let this thread die: the periodic work would stop
                # silently and stay stopped for the life of the process.
                logger.warning(
                    "%s background tick failed, continuing: %s",
                    self._background_task_name(), e)

            # sleep in slices so stop() does not block for a full interval
            slept = 0
            while self._bg_running and slept < self.BG_INTERVAL_SECONDS:
                time.sleep(self.BG_SLEEP_SLICE_SECONDS)
                slept += self.BG_SLEEP_SLICE_SECONDS

    def start(self):
        # Locked: "if not running: running = True; spawn" is check-then-act, so
        # concurrent callers could each spawn a thread. Only the last would be
        # reachable; the rest ran orphaned for the process lifetime.
        with self._lifecycle_lock:
            if self._bg_running:
                return
            self._bg_running = True
            self._bg_thread = threading.Thread(target=self.background_task, daemon=True)
            self._bg_thread.start()

    def stop(self):
        with self._lifecycle_lock:
            if not self._bg_running:
                return
            self._bg_running = False
            thread = self._bg_thread
            self._bg_thread = None

        # joined outside the lock: holding it across a join is how lifecycle
        # code deadlocks against the very thread it is waiting on
        if thread is not None:
            thread.join(timeout=self.BG_JOIN_TIMEOUT_SECONDS)
            if thread.is_alive():
                logger.warning(
                    "%s background thread did not stop within %ss; it is a "
                    "daemon thread and will not block exit.",
                    self._background_task_name(), self.BG_JOIN_TIMEOUT_SECONDS)

    def is_running(self):
        return self._bg_running
