"""Task B: the shared background-task lifecycle.

VitalSigns and VitalService each hand-rolled this loop, and the copies drifted --
the registry fix repaired one while the identical bugs stayed live in the other.
These tests pin the mixin's guarantees directly, so a regression is caught once
rather than once per copy.
"""

import logging
import threading
import time

import pytest

from vital_ai_vitalsigns.utils.background_task import BackgroundTaskMixin


class Ticker(BackgroundTaskMixin):
    """Minimal subclass with a fast interval, for testing the mixin itself."""

    BG_INTERVAL_SECONDS = 0.05
    BG_SLEEP_SLICE_SECONDS = 0.01
    BG_JOIN_TIMEOUT_SECONDS = 5

    def __init__(self, on_tick=None):
        self._init_background_task()
        self.ticks = []
        self._on_tick = on_tick

    def _background_tick(self):
        self.ticks.append(1)
        if self._on_tick is not None:
            self._on_tick()


def wait_for(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


class TestLoopGuarantees:

    def test_ticks_repeatedly(self):
        t = Ticker()
        t.start()
        try:
            assert wait_for(lambda: len(t.ticks) >= 3), f"only {len(t.ticks)} ticks"
        finally:
            t.stop()

    def test_thread_survives_a_raising_tick(self, caplog):
        """The bug that turned a rare KeyError into an unbounded leak: one
        exception killed the thread permanently, with nothing logged."""
        def boom():
            raise RuntimeError("simulated tick failure")

        t = Ticker(on_tick=boom)
        with caplog.at_level(logging.WARNING):
            t.start()
            try:
                assert wait_for(lambda: len(t.ticks) >= 3), (
                    f"thread stopped after {len(t.ticks)} failing tick(s)")
                assert t._bg_thread.is_alive()
            finally:
                t.stop()

        assert any("background tick failed" in r.message for r in caplog.records), \
            "the failure was swallowed without a log"

    def test_stop_is_prompt(self):
        """A coarse sleep(interval) made stop() block for a full interval."""
        t = Ticker()
        t.BG_INTERVAL_SECONDS = 30  # long interval, sliced sleep
        t.BG_SLEEP_SLICE_SECONDS = 0.01
        t.start()
        assert wait_for(lambda: len(t.ticks) >= 1)

        started = time.monotonic()
        t.stop()
        elapsed = time.monotonic() - started

        assert not t.is_running()
        assert elapsed < 5, f"stop() took {elapsed:.1f}s despite a sliced sleep"

    def test_stop_clears_state(self):
        t = Ticker()
        t.start()
        t.stop()
        assert not t.is_running()
        assert t._bg_thread is None


class TestLifecycleRaces:

    def test_concurrent_start_spawns_one_thread(self):
        t = Ticker()
        before = set(threading.enumerate())
        barrier = threading.Barrier(8)

        def worker():
            barrier.wait(timeout=10)
            t.start()

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=30)

        try:
            orphans = [x for x in threading.enumerate()
                       if x not in before and x.is_alive() and x is not t._bg_thread
                       and x not in threads]
            assert orphans == [], f"start() orphaned {len(orphans)} thread(s)"
        finally:
            t.stop()

    def test_concurrent_stop_converges(self):
        t = Ticker()
        t.start()
        barrier = threading.Barrier(8)
        errors = []

        def worker():
            try:
                barrier.wait(timeout=10)
                t.stop()
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=30)

        assert not errors, f"concurrent stop() raised: {errors[:3]}"
        assert not t.is_running()
        assert t._bg_thread is None

    def test_start_stop_cycles(self):
        t = Ticker()
        seen = []
        for _ in range(5):
            t.start()
            assert t.is_running()
            seen.append(t._bg_thread)
            t.stop()
            assert not t.is_running()

        assert not any(th.is_alive() for th in seen), "a previous thread was orphaned"

    def test_double_start_does_not_replace_the_thread(self):
        t = Ticker()
        t.start()
        try:
            first = t._bg_thread
            t.start()
            assert t._bg_thread is first
        finally:
            t.stop()

    def test_double_stop_is_idempotent(self):
        t = Ticker()
        t.start()
        t.stop()
        t.stop()
        assert not t.is_running()


class TestBothClassesUseTheMixin:
    """The point of Task B: one implementation, so a fix can't reach only one."""

    def test_vitalsigns_uses_the_mixin(self):
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        assert issubclass(VitalSigns, BackgroundTaskMixin)

    def test_vitalservice_uses_the_mixin(self):
        from vital_ai_vitalsigns.service.vital_service import VitalService
        assert issubclass(VitalService, BackgroundTaskMixin)

    @pytest.mark.parametrize("method", ["start", "stop", "is_running", "background_task"])
    def test_neither_class_reimplements_the_lifecycle(self, method):
        from vital_ai_vitalsigns.vitalsigns import VitalSigns
        from vital_ai_vitalsigns.service.vital_service import VitalService

        for cls in (VitalSigns, VitalService):
            assert method not in vars(cls), (
                f"{cls.__name__} re-implements {method}(); that divergence is "
                f"exactly what let the same bugs live in two copies")

    def test_legacy_attribute_names_still_work(self):
        """Back-compat: the two classes historically used different names for
        the same state, and callers (including tests) touch them."""
        from vital_ai_vitalsigns.service.vital_service import VitalService

        svc = VitalService(vitalservice_name="legacy-test",
                           synchronize_service=False, synchronize_task=False)
        assert svc.running is False
        assert svc.background_thread is None

        svc.start()
        try:
            assert svc.running is True
            assert svc.background_thread is svc._bg_thread
        finally:
            svc.stop()
        assert svc.running is False
        assert svc.background_thread is None
