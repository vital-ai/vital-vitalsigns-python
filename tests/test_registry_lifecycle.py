"""Tests for the GraphObject/GraphCollection registry and the reaper thread.

Regression cover for a leak under concurrent GraphObject churn: the registry
maps were mutated without the lock the 60s sweep held, so a KeyError could
escape clean_graph_object_map -> cleanup_task -> background_task and kill the
reaper thread permanently. The maps are now WeakValueDictionaries that
self-evict, so there is no sweep to race against.
"""

import gc
import threading
import time

import pytest


@pytest.fixture(autouse=True)
def _enable_registry(registry_enabled):
    """The object registry is opt-in (default off); these tests assert on it."""



def test_object_self_evicts(vs, make_node):
    """Dropping the last reference removes the registry entry, with no sweep."""
    before = vs.graph_object_count()

    node = make_node("evict")
    assert vs.graph_object_count() == before + 1, "object was not registered"

    del node
    gc.collect()

    assert vs.graph_object_count() == before, "object did not self-evict"


def test_cycle_self_evicts(vs, make_node, new_collection):
    """A GraphObject <-> GraphCollection cycle evicts after a collect."""
    before_obj = vs.graph_object_count()
    before_coll = vs.graph_collection_count()

    collection = new_collection()
    node = make_node("cycle")
    collection.add(node)

    del collection
    del node
    gc.collect()

    assert vs.graph_object_count() == before_obj, "cyclic object leaked"
    assert vs.graph_collection_count() == before_coll, "cyclic collection leaked"


def test_remove_is_idempotent(vs, make_node, new_collection):
    """remove_* is safe to call repeatedly; it must never raise KeyError."""
    node = make_node("idempotent")
    vs.remove_graph_object(node)
    vs.remove_graph_object(node)

    collection = new_collection()
    vs.remove_graph_collection(collection)
    vs.remove_graph_collection(collection)


def test_sweep_methods_are_noops(vs):
    """The deprecated sweep entry points still exist and do nothing."""
    assert vs.clean_graph_object_map() == 0
    assert vs.clean_graph_collection_map() == 0


def test_no_finalizers_on_registry_types(make_node, new_collection):
    """__del__ was removed from both types; a finalizer would re-add per-object
    teardown cost and force the cycle collector to run it individually.

    Walks the MRO rather than using hasattr: GraphObjectMeta defines __getattr__,
    so hasattr(cls, anything) is True and would make this assertion vacuous.
    """
    node = make_node("finalizer")
    collection = new_collection()

    def defines_del(obj):
        return [k.__name__ for k in type(obj).__mro__ if "__del__" in vars(k)]

    assert defines_del(node) == [], f"GraphObject regained a __del__: {defines_del(node)}"
    assert defines_del(collection) == [], \
        f"GraphCollection regained a __del__: {defines_del(collection)}"


def test_concurrent_churn_keeps_registry_bounded_and_reaper_alive(vs, make_node, new_collection):
    """The original failure mode: heavy concurrent create/destroy while the
    reaper runs. The registry must drain and the background thread must survive."""
    assert vs.is_running(), "background thread not running"

    errors = []
    n_threads = 8
    per_thread = 300

    def churn(tid):
        try:
            for i in range(per_thread):
                nodes = [make_node(f"{tid}-{i}-{j}") for j in range(5)]
                collection = new_collection()
                for n in nodes:
                    collection.add(n)
                del nodes
                del collection
                if i % 50 == 0:
                    # exercise the iterating reader concurrently with writers
                    vs.graph_collection_set()
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    workers = [threading.Thread(target=churn, args=(t,)) for t in range(n_threads)]
    for w in workers:
        w.start()
    # force collects concurrently with the churn
    for _ in range(5):
        vs.cleanup_task()
        time.sleep(0.05)
    for w in workers:
        w.join(timeout=120)

    assert not any(w.is_alive() for w in workers), "churn threads did not finish"
    assert not errors, f"errors during concurrent churn: {errors[:3]}"

    gc.collect()
    total = n_threads * per_thread * 5
    remaining = vs.graph_object_count()
    assert remaining < 100, f"registry not bounded: {remaining} entries after {total} objects"

    assert vs.is_running(), "background thread stopped"
    assert vs._background_thread.is_alive(), "background thread died"


def test_graph_collection_set_safe_under_concurrent_writers(vs, new_collection):
    """Iterating the collection map while other threads register must not raise
    'dictionary changed size during iteration'."""
    errors = []
    stop = threading.Event()

    def writer():
        try:
            while not stop.is_set():
                held = [new_collection() for _ in range(20)]
                del held
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    def reader():
        try:
            while not stop.is_set():
                vs.graph_collection_set()
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=writer) for _ in range(4)]
    threads += [threading.Thread(target=reader) for _ in range(4)]
    for t in threads:
        t.start()
    time.sleep(1.0)
    stop.set()
    for t in threads:
        t.join(timeout=30)

    assert not errors, f"errors during concurrent iteration: {errors[:3]}"


def test_reaper_survives_a_failing_cleanup(vs, monkeypatch):
    """background_task must swallow and log any cleanup_task error.

    A reaper that dies on one transient exception is what turned a rare KeyError
    into an unbounded leak: the periodic collect stopped for the process
    lifetime, with nothing logged.
    """
    was_running = vs.is_running()
    if was_running:
        vs.stop()

    calls = []

    def exploding_cleanup():
        calls.append(1)
        raise RuntimeError("simulated cleanup failure")

    # tighten the loop so several iterations fit in the test window. These are
    # class attributes on BackgroundTaskMixin, read via self.
    monkeypatch.setattr(type(vs), "BG_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr(type(vs), "BG_SLEEP_SLICE_SECONDS", 0.01)
    monkeypatch.setattr(vs, "cleanup_task", exploding_cleanup)

    try:
        vs._running = True
        thread = threading.Thread(target=vs.background_task, daemon=True)
        thread.start()

        deadline = time.monotonic() + 10
        while len(calls) < 3 and time.monotonic() < deadline:
            time.sleep(0.05)

        assert len(calls) >= 3, (
            f"reaper stopped after {len(calls)} failing iteration(s); "
            "it must keep going")
        assert thread.is_alive(), "reaper thread died on a cleanup failure"
    finally:
        vs._running = False
        thread.join(timeout=10)
        assert not thread.is_alive(), "reaper thread did not shut down"
        if was_running:
            vs.start()


class TestLifecycle:
    """stop()/start() must be prompt and repeatable.

    These tests mutate shared singleton state, so each one establishes its own
    precondition and restores a running reaper on the way out -- they must not
    depend on the order they run in, or on having run only once. (An earlier
    draft asserted `vs.is_running()` on entry to test_stop_is_prompt, which held
    only on the first execution; the CI stress job, which repeats each test 10x,
    caught it.)
    """

    @pytest.fixture(autouse=True)
    def reaper_running(self, vs):
        if not vs.is_running():
            vs.start()
        yield
        if not vs.is_running():
            vs.start()

    def test_stop_is_prompt(self, vs):
        assert vs.is_running(), "fixture did not establish a running reaper"

        started = time.monotonic()
        vs.stop()
        elapsed = time.monotonic() - started

        assert not vs.is_running()
        assert vs._background_thread is None
        # the loop sleeps in slices; a full-interval sleep would block ~60s here
        assert elapsed < 10, f"stop() took {elapsed:.1f}s, expected prompt shutdown"

    def test_restart_after_stop(self, vs):
        vs.stop()
        assert not vs.is_running()

        vs.start()
        assert vs.is_running()
        assert vs._background_thread is not None
        assert vs._background_thread.is_alive()

    def test_double_start_is_idempotent(self, vs):
        thread = vs._background_thread
        assert thread is not None

        vs.start()
        assert vs._background_thread is thread, "second start() spawned a new thread"
        assert thread.is_alive()

    def test_double_stop_is_idempotent(self, vs):
        vs.stop()
        vs.stop()
        assert not vs.is_running()
        assert vs._background_thread is None

    def test_stop_start_cycles_repeatedly(self, vs):
        """Several stop/start cycles in a row must not leak or orphan threads."""
        seen = []
        for _ in range(5):
            vs.stop()
            assert not vs.is_running()
            vs.start()
            assert vs.is_running()
            seen.append(vs._background_thread)

        assert all(t.is_alive() for t in seen[-1:]), "final reaper thread is dead"
        for old in seen[:-1]:
            assert not old.is_alive(), "a previous reaper thread was left running"
