"""Race tests for background-thread lifecycle (C1, C2).

Both VitalSigns and VitalService had the same check-then-act bug:

    if not self.running:          # thread A and B both pass
        self.running = True
        self.thread = Thread(...) # only the last is reachable; the rest orphan

Race windows here are narrow, so these tests force aggressive GIL switching via
sys.setswitchinterval and repeat across trials. A race test that passes because
it never triggered the race is worse than no test, so each one is written to
fail against the unfixed implementation -- see test_unfixed_start_pattern_races,
which pins that the detection method actually works.
"""

import logging
import sys
import threading
import time

import pytest

from vital_ai_vitalsigns.service.vital_service import VitalService


@pytest.fixture
def fast_switching():
    """Force the interpreter to switch threads aggressively for the test."""
    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    yield
    sys.setswitchinterval(previous)


def hammer(fn, n_threads=8):
    """Run fn() on n_threads simultaneously, released by a barrier."""
    barrier = threading.Barrier(n_threads)
    errors = []

    def worker():
        try:
            barrier.wait(timeout=30)
            fn()
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not any(t.is_alive() for t in threads), "worker threads did not finish"
    assert not errors, f"errors during concurrent access: {errors[:3]}"


def make_service(**kwargs):
    """A VitalService with no backing stores and no startup synchronization."""
    kwargs.setdefault("vitalservice_name", "test-service")
    kwargs.setdefault("synchronize_service", False)
    kwargs.setdefault("synchronize_task", False)
    return VitalService(**kwargs)


# --------------------------------------------------------------------------
# meta: prove the detection method catches the original bug
# --------------------------------------------------------------------------

def test_unfixed_start_pattern_races(fast_switching):
    """The original check-then-act start() must be shown to actually race.

    If this ever stops detecting duplicate threads, the tests below are proving
    nothing and the harness needs revisiting.
    """

    class Unfixed:
        def __init__(self):
            self.running = False
            self.thread = None
            self.spawned = []

        def loop(self):
            time.sleep(0.2)

        def start(self):
            if not self.running:
                time.sleep(0)  # the real check -> act gap
                self.running = True
                t = threading.Thread(target=self.loop, daemon=True)
                self.thread = t
                t.start()
                self.spawned.append(t)

    worst = 0
    for _ in range(20):
        obj = Unfixed()
        hammer(obj.start)
        worst = max(worst, len(obj.spawned))

    assert worst > 1, (
        "the unfixed start() pattern did not race under forced switching; "
        "the concurrency tests below cannot be trusted to detect a regression")


# --------------------------------------------------------------------------
# C1 -- VitalSigns
# --------------------------------------------------------------------------

class TestVitalSignsLifecycle:

    @pytest.fixture(autouse=True)
    def reaper_running(self, vs):
        if not vs.is_running():
            vs.start()
        yield
        if not vs.is_running():
            vs.start()

    def test_concurrent_start_spawns_exactly_one_thread(self, vs, fast_switching):
        vs.stop()
        assert not vs.is_running()

        before = set(threading.enumerate())
        hammer(vs.start)

        assert vs.is_running()
        reapers = [t for t in threading.enumerate()
                   if t not in before and t.is_alive() and t is not vs._background_thread]

        assert vs._background_thread is not None
        assert vs._background_thread.is_alive()
        assert reapers == [], f"concurrent start() orphaned {len(reapers)} thread(s): {reapers}"

    def test_concurrent_stop_converges(self, vs, fast_switching):
        if not vs.is_running():
            vs.start()

        hammer(vs.stop)

        assert not vs.is_running()
        assert vs._background_thread is None

    def test_concurrent_start_stop_mix_leaves_consistent_state(self, vs, fast_switching):
        """Interleaved start/stop must not leave running=True with no thread,
        or running=False with a live thread."""
        def churn():
            for _ in range(20):
                vs.start()
                vs.stop()

        hammer(churn, n_threads=4)

        # settle on a known state
        vs.stop()
        assert not vs.is_running()
        assert vs._background_thread is None

        vs.start()
        assert vs.is_running()
        assert vs._background_thread is not None and vs._background_thread.is_alive()


# --------------------------------------------------------------------------
# C2 -- VitalService
# --------------------------------------------------------------------------

class TestVitalServiceLifecycle:

    def test_starts_and_stops(self):
        service = make_service()
        assert not service.is_running()

        service.start()
        assert service.is_running()
        assert service.background_thread.is_alive()

        service.stop()
        assert not service.is_running()
        assert service.background_thread is None

    def test_stop_is_prompt(self):
        """The loop slept a full 60s interval; stop() joined it without timeout,
        so shutting down N services could take N minutes."""
        service = make_service()
        service.start()
        time.sleep(0.1)

        started = time.monotonic()
        service.stop()
        elapsed = time.monotonic() - started

        assert not service.is_running()
        assert elapsed < 10, f"stop() took {elapsed:.1f}s, expected prompt shutdown"

    def test_concurrent_start_spawns_exactly_one_thread(self, fast_switching):
        service = make_service()
        before = set(threading.enumerate())

        hammer(service.start)

        orphans = [t for t in threading.enumerate()
                   if t not in before and t.is_alive() and t is not service.background_thread]
        assert orphans == [], f"concurrent start() orphaned {len(orphans)} thread(s)"
        assert service.background_thread is not None
        service.stop()

    def test_concurrent_stop_converges(self, fast_switching):
        service = make_service()
        service.start()

        hammer(service.stop)

        assert not service.is_running()
        assert service.background_thread is None

    def test_background_task_survives_failing_refresh(self, monkeypatch, caplog):
        """query_graph_info raising must not kill the thread. It is a stub today,
        so this guard is latent -- which is exactly when it silently rots."""
        monkeypatch.setattr(VitalService, "BG_INTERVAL_SECONDS", 0.05)
        monkeypatch.setattr(VitalService, "BG_SLEEP_SLICE_SECONDS", 0.01)

        service = make_service()
        calls = []

        def exploding():
            calls.append(1)
            raise RuntimeError("simulated refresh failure")

        monkeypatch.setattr(service, "query_graph_info", exploding)

        with caplog.at_level(logging.WARNING):
            service.start()
            deadline = time.monotonic() + 10
            while len(calls) < 3 and time.monotonic() < deadline:
                time.sleep(0.05)

        try:
            assert len(calls) >= 3, (
                f"thread stopped after {len(calls)} failing refresh(es); it must keep going")
            assert service.background_thread.is_alive(), "thread died on a refresh failure"
            assert any("background tick failed" in r.message for r in caplog.records), \
                "failure was swallowed without a log"
        finally:
            service.stop()

    def test_many_services_stop_quickly(self):
        """N services must not serialize into an N-interval shutdown."""
        services = [make_service(vitalservice_name=f"svc-{i}") for i in range(5)]
        for s in services:
            s.start()
        time.sleep(0.1)

        started = time.monotonic()
        for s in services:
            s.stop()
        elapsed = time.monotonic() - started

        assert all(not s.is_running() for s in services)
        assert elapsed < 15, (
            f"stopping {len(services)} services took {elapsed:.1f}s; "
            "shutdown is serializing on the sleep interval")
