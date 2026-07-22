"""Tests for VitalSignsMeta, the singleton metaclass.

Regression cover for a latent hard deadlock: the previous implementation used a
non-reentrant Lock and only published the instance after __init__ returned, so
any call to VitalSigns() from inside VitalSigns.__init__ blocked forever on a
lock its own thread already held. GraphObject.__init__ calls VitalSigns(), so
constructing any GraphObject during startup would have hung the process.
"""

import threading
import time

import pytest

from vital_ai_vitalsigns.vitalsigns import VitalSignsMeta


@pytest.fixture
def isolated_meta():
    """A private copy of the metaclass, so tests never touch the real singleton."""

    class Meta(VitalSignsMeta):
        _instances = {}
        _lock = threading.RLock()
        _building = threading.local()

    return Meta


def run_with_timeout(fn, timeout=10.0):
    """Run fn in a thread; return (completed, result_or_exc). Detects deadlock."""
    box = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as e:  # noqa: BLE001 - recorded and re-raised by caller
            box["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return False, None
    if "error" in box:
        raise box["error"]
    return True, box.get("result")


def test_reentrant_construction_does_not_deadlock(isolated_meta):
    """A nested Thing() inside Thing.__init__ must return, not hang.

    This is the exact shape of GraphObject.__init__ -> VitalSigns() during
    VitalSigns.__init__. Before the fix this blocked forever.
    """
    inits = []

    class Thing(metaclass=isolated_meta):
        def __init__(self):
            inits.append(1)
            self.nested = Thing()

    completed, thing = run_with_timeout(Thing)

    assert completed, "re-entrant construction deadlocked"
    assert len(inits) == 1, f"__init__ ran {len(inits)} times, expected 1"
    assert thing.nested is thing, "re-entrant call returned a different instance"


def test_reentrant_call_sees_same_instance_after_completion(isolated_meta):
    """The instance handed to a re-entrant caller is the one finally published."""
    captured = {}

    class Thing(metaclass=isolated_meta):
        def __init__(self):
            captured["during"] = Thing()

    completed, thing = run_with_timeout(Thing)

    assert completed
    assert captured["during"] is thing
    assert Thing() is thing, "later calls returned a different instance"


def test_concurrent_first_construction_runs_init_once(isolated_meta):
    """N threads racing the first construction: exactly one __init__, one object."""
    init_count = []
    barrier = threading.Barrier(16)
    results = []
    errors = []

    class Thing(metaclass=isolated_meta):
        def __init__(self):
            init_count.append(1)
            # widen the window so a broken double-checked lock would lose the race
            time.sleep(0.2)
            self.ready = True

    def worker():
        try:
            barrier.wait(timeout=10)
            obj = Thing()
            # no thread may observe a half-built singleton
            assert getattr(obj, "ready", False), "observed partially built instance"
            results.append(obj)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"errors during concurrent construction: {errors[:3]}"
    assert not any(t.is_alive() for t in threads), "threads did not finish"
    assert len(init_count) == 1, f"__init__ ran {len(init_count)} times, expected 1"
    assert len(results) == 16
    assert len(set(map(id, results))) == 1, "threads got different instances"


def test_failed_init_is_not_cached(isolated_meta):
    """A constructor that raises must not leave a broken singleton behind."""
    attempts = []

    class Thing(metaclass=isolated_meta):
        def __init__(self):
            attempts.append(1)
            if len(attempts) == 1:
                raise ValueError("boom")
            self.ok = True

    with pytest.raises(ValueError):
        Thing()

    thing = Thing()
    assert thing.ok is True
    assert len(attempts) == 2, "second call did not retry construction"


def test_failed_init_does_not_leak_building_state(isolated_meta):
    """After a failed construction the thread-local build slot is cleared."""

    class Thing(metaclass=isolated_meta):
        def __init__(self):
            raise ValueError("boom")

    with pytest.raises(ValueError):
        Thing()

    building = getattr(isolated_meta._building, "map", {})
    assert Thing not in building, "in-progress instance left in thread-local"


def test_args_on_already_built_singleton_warn(isolated_meta, caplog):
    """VitalSigns(background_task=False) after construction is silently ignored;
    it must at least warn rather than appear to take effect."""

    class Thing(metaclass=isolated_meta):
        def __init__(self, flag=True):
            self.flag = flag

    first = Thing(flag=True)

    with caplog.at_level("WARNING"):
        second = Thing(flag=False)

    assert second is first
    assert second.flag is True, "arguments unexpectedly applied"
    assert any("already constructed" in r.message for r in caplog.records), \
        "no warning emitted for ignored construction arguments"
