"""Race tests for VitalServiceManager lazy initialization (C3, C4).

Four accessors shared this shape:

    if self.initialized is False:
        self._initialize()

Two threads could both see False and both run _initialize(), each constructing
the full set of VitalService objects -- each of which spawns a background
thread. Only one services map survived; the other set's threads ran orphaned.

_initialize() also began with `self.services = {}` and repopulated
incrementally, so a concurrent reader could see an empty or half-built map and
raise KeyError for a correctly configured service.
"""

import sys
import threading
import time

import pytest

from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager


@pytest.fixture
def fast_switching():
    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    yield
    sys.setswitchinterval(previous)


class FakeService:
    """Stand-in for VitalService: records construction and stop() calls."""

    def __init__(self, name):
        self.vitalservice_name = name
        self.stopped = False

    def stop(self):
        self.stopped = True


def make_manager(n_services=5, build_delay=0.0, constructed=None):
    """A manager whose _initialize builds n_services, with an injectable delay
    to widen the window a concurrent reader could observe."""
    manager = VitalServiceManager()

    def fake_initialize():
        services = {}
        for i in range(n_services):
            svc = FakeService(f"svc-{i}")
            if constructed is not None:
                constructed.append(svc)
            if build_delay:
                time.sleep(build_delay)
            services[svc.vitalservice_name] = svc
        manager.services = services
        manager.initialized = True

    manager._initialize = fake_initialize
    return manager


def hammer(fn, n_threads=8, timeout=60):
    barrier = threading.Barrier(n_threads)
    errors = []
    results = []

    def worker():
        try:
            barrier.wait(timeout=30)
            results.append(fn())
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout)
    assert not any(t.is_alive() for t in threads), "worker threads did not finish"
    return results, errors


# --------------------------------------------------------------------------
# meta: prove the detection method catches the original bug
# --------------------------------------------------------------------------

def test_unfixed_lazy_init_pattern_races(fast_switching):
    """The original unlocked check-then-act must be shown to actually
    double-initialize, or the tests below prove nothing."""

    class Unfixed:
        def __init__(self):
            self.initialized = False
            self.services = {}
            self.init_count = 0

        def _initialize(self):
            self.init_count += 1
            time.sleep(0)
            self.services = {f"svc-{i}": i for i in range(5)}
            self.initialized = True

        def get(self):
            if self.initialized is False:
                self._initialize()
            return self.services

    worst = 0
    for _ in range(20):
        obj = Unfixed()
        hammer(obj.get)
        worst = max(worst, obj.init_count)

    assert worst > 1, (
        "the unfixed lazy-init pattern did not double-initialize under forced "
        "switching; the tests below cannot be trusted to detect a regression")


# --------------------------------------------------------------------------
# C3
# --------------------------------------------------------------------------

def test_concurrent_first_access_initializes_once(fast_switching):
    """Every duplicate _initialize() would have constructed a duplicate set of
    VitalService objects, each spawning an orphaned background thread."""
    for _ in range(10):
        constructed = []
        manager = make_manager(n_services=5, constructed=constructed)

        _, errors = hammer(manager.get_vitalservice_list)

        assert not errors, f"errors during concurrent init: {errors[:3]}"
        assert len(constructed) == 5, (
            f"_initialize() ran more than once: {len(constructed)} services built, "
            f"expected 5 (the surplus would each own an orphaned thread)")
        assert manager.initialized


def test_concurrent_readers_never_see_a_partial_map(fast_switching):
    """No reader may observe an empty or half-built services map."""
    for _ in range(5):
        manager = make_manager(n_services=5, build_delay=0.002)
        observed = []
        errors = []

        def read():
            try:
                observed.append(len(manager.get_vitalservice_list()))
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        hammer(read, n_threads=8)

        assert not errors, f"reader raised during initialization: {errors[:3]}"
        assert observed, "no observations recorded"
        assert set(observed) == {5}, (
            f"readers observed partial service maps: sizes {sorted(set(observed))}")


def test_concurrent_get_vitalservice_by_name(fast_switching):
    """get_vitalservice() raised KeyError against the empty-map window."""
    manager = make_manager(n_services=5, build_delay=0.002)

    results, errors = hammer(lambda: manager.get_vitalservice("svc-3"), n_threads=8)

    assert not errors, f"get_vitalservice raised during init: {errors[:3]}"
    assert all(r.vitalservice_name == "svc-3" for r in results)


def test_set_config_resets_under_lock(fast_switching):
    """set_config() clears state that readers use; it must not expose a window."""
    manager = make_manager(n_services=5)
    manager.get_vitalservice_list()
    assert manager.initialized

    manager.set_config("some-config.yaml")
    assert not manager.initialized
    assert manager.services == {}


# --------------------------------------------------------------------------
# C7 -- discarded services must be stopped, not orphaned
# --------------------------------------------------------------------------

def test_set_config_stops_discarded_services():
    """VitalService spawns a background thread by default. Dropping the services
    map without stopping them leaked one thread per service, permanently."""
    constructed = []
    manager = make_manager(n_services=4, constructed=constructed)
    manager.get_vitalservice_list()
    assert len(constructed) == 4

    manager.set_config("other-config.yaml")

    unstopped = [s.vitalservice_name for s in constructed if not s.stopped]
    assert unstopped == [], f"services discarded without stop(): {unstopped}"


def test_reinitialize_stops_previous_generation():
    """Uses the REAL _initialize (no config -> the empty branch), so this
    exercises the shipped retirement logic rather than the test's stub."""
    manager = VitalServiceManager()
    first_generation = [FakeService(f"svc-{i}") for i in range(3)]
    manager.services = {s.vitalservice_name: s for s in first_generation}
    manager.initialized = True

    manager._initialize()

    unstopped = [s.vitalservice_name for s in first_generation if not s.stopped]
    assert unstopped == [], f"previous generation left running: {unstopped}"


def test_shutdown_stops_everything_and_is_idempotent():
    constructed = []
    manager = make_manager(n_services=4, constructed=constructed)
    manager.get_vitalservice_list()

    manager.shutdown()
    assert all(s.stopped for s in constructed)
    assert manager.services == {}
    assert not manager.initialized

    manager.shutdown()  # must not raise


def test_remove_vitalservice_stops_the_removed_service():
    constructed = []
    manager = make_manager(n_services=3, constructed=constructed)
    manager.get_vitalservice_list()
    target = next(s for s in constructed if s.vitalservice_name == "svc-1")

    assert manager.remove_vitalservice("svc-1") is True
    assert target.stopped, "removed service was not stopped; its thread leaks"

    others = [s for s in constructed if s is not target]
    assert not any(s.stopped for s in others), "removal stopped unrelated services"


def test_stop_failure_does_not_abort_the_sweep():
    """One service raising in stop() must not prevent the rest from stopping."""
    class BadService(FakeService):
        def stop(self):
            raise RuntimeError("cannot stop")

    manager = VitalServiceManager()
    good_a, good_b = FakeService("a"), FakeService("b")
    manager.services = {"a": good_a, "bad": BadService("bad"), "b": good_b}
    manager.initialized = True

    manager.shutdown()  # must not propagate

    assert good_a.stopped and good_b.stopped, "a failing stop() aborted the sweep"


# --------------------------------------------------------------------------
# C4
# --------------------------------------------------------------------------

def test_remove_vitalservice_is_idempotent():
    """Was a bare `del self.services[name]` -- KeyError on double remove."""
    manager = make_manager(n_services=3)
    manager.get_vitalservice_list()

    assert manager.remove_vitalservice("svc-1") is True
    assert manager.remove_vitalservice("svc-1") is False
    assert manager.remove_vitalservice("never-existed") is False


def test_concurrent_remove_does_not_raise(fast_switching):
    """Concurrent removal of the same service must not raise KeyError."""
    manager = make_manager(n_services=3)
    manager.get_vitalservice_list()

    results, errors = hammer(lambda: manager.remove_vitalservice("svc-2"), n_threads=8)

    assert not errors, f"concurrent remove raised: {errors[:3]}"
    assert sum(1 for r in results if r) == 1, "more than one caller claimed the removal"


def test_add_and_remove_concurrently(fast_switching):
    """Mixed add/remove must leave the map consistent and never raise."""
    manager = make_manager(n_services=3)
    manager.get_vitalservice_list()
    errors = []

    def churn(tid):
        try:
            for i in range(50):
                name = f"churn-{tid}-{i}"
                manager.add_vitalservice(name, FakeService(name))
                manager.remove_vitalservice(name)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=churn, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not any(t.is_alive() for t in threads)
    assert not errors, f"errors during concurrent add/remove: {errors[:3]}"
    leftover = [k for k in manager.services if k.startswith("churn-")]
    assert leftover == [], f"churned services left behind: {leftover[:5]}"
