"""Soak tests asserting the reported symptom directly: resident memory.

The original bug report was "RSS climbs in a sawtooth toward the container
limit". Entry counts are a proxy; these tests measure process memory so a leak
that bypasses the registry (a cache pinning objects, a finalizer resurrecting
them) is still caught.

Budget calibration -- measured on this codebase, 20,000 iterations
(220,000 GraphObjects) after a 500-iteration warmup:

    no leak                    1.2 MB peak-RSS growth
    every collection retained  269.6 MB peak-RSS growth

RSS_BUDGET sits at 48 MB: 40x headroom over the clean run so CI noise cannot
fail it, and 5.6x below the leak signal so a real regression cannot pass. An
earlier draft of this file used 2,000 iterations against a 96 MB budget, which a
genuine 22,000-object leak cleared at only 25.7 MB -- the test was vacuous.
test_harness_detects_an_injected_leak guards against that regressing again.

Marked `slow` -- run with `-m slow` or as part of the full CI job.
"""

import gc
import resource
import sys
import threading

import pytest

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def _enable_registry(registry_enabled):
    """The object registry is opt-in (default off); these tests assert on it."""


MB = 1024 * 1024

# see calibration note above
WARMUP_ITERS = 500
SOAK_ITERS = 20_000
RSS_BUDGET = 48 * MB

OBJECTS_PER_ITER = 11  # 10 nodes + 1 collection


def peak_rss_bytes():
    """Peak RSS of this process. ru_maxrss is bytes on macOS, KiB on Linux."""
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def current_rss_bytes():
    """Current RSS, or None if it can't be read without extra dependencies."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/statm") as fh:
                pages = int(fh.read().split()[1])
            return pages * resource.getpagesize()
        except (OSError, IndexError, ValueError):
            return None
    try:
        import psutil
    except ImportError:
        return None
    return psutil.Process().memory_info().rss


def churn_once(make_node, new_collection, tag, retain=None):
    """One unit of work: a small cyclic object graph, then dropped.

    If `retain` is a list the collection is appended to it, simulating a leak.
    """
    nodes = [make_node(f"{tag}-{j}") for j in range(10)]
    collection = new_collection()
    for n in nodes:
        collection.add(n)
    if retain is not None:
        retain.append(collection)


def run_churn(make_node, new_collection, iters, prefix, retain=None):
    for i in range(iters):
        churn_once(make_node, new_collection, f"{prefix}-{i}", retain=retain)
    gc.collect()


def test_rss_bounded_under_sustained_churn(vs, make_node, new_collection):
    """Peak RSS must plateau, not grow with the number of objects created.

    Warm up first so one-time costs (imports, ontology caches, allocator arena
    growth) land in the baseline; then do the real work and require the peak
    barely moves.
    """
    run_churn(make_node, new_collection, WARMUP_ITERS, "warmup")

    baseline_peak = peak_rss_bytes()
    baseline_objs = vs.graph_object_count()

    run_churn(make_node, new_collection, SOAK_ITERS, "soak")

    growth = peak_rss_bytes() - baseline_peak
    leaked = vs.graph_object_count() - baseline_objs

    assert growth < RSS_BUDGET, (
        f"peak RSS grew {growth / MB:.1f} MB over {SOAK_ITERS} iterations "
        f"({SOAK_ITERS * OBJECTS_PER_ITER} objects); "
        f"budget is {RSS_BUDGET / MB:.0f} MB")
    assert leaked < 100, f"registry grew by {leaked} entries during the soak"


def test_harness_detects_an_injected_leak(vs, make_node, new_collection):
    """The soak assertion must actually be capable of failing.

    Retains every collection created, then asserts the same budget the soak test
    uses would be blown. Without this, shrinking the iteration count or raising
    the budget could silently turn the soak tests into no-ops.
    """
    leaked_objects = []

    run_churn(make_node, new_collection, WARMUP_ITERS, "leakwarm")
    baseline_peak = peak_rss_bytes()

    try:
        run_churn(make_node, new_collection, SOAK_ITERS, "leak", retain=leaked_objects)
        growth = peak_rss_bytes() - baseline_peak

        assert growth > RSS_BUDGET, (
            f"an injected leak of {len(leaked_objects) * OBJECTS_PER_ITER} objects grew "
            f"peak RSS by only {growth / MB:.1f} MB, which is under the "
            f"{RSS_BUDGET / MB:.0f} MB budget -- the soak tests cannot detect a real "
            f"leak. Raise SOAK_ITERS or lower RSS_BUDGET.")
    finally:
        leaked_objects.clear()
        gc.collect()


def test_rss_bounded_under_concurrent_churn(vs, make_node, new_collection):
    """Same assertion under the concurrency that triggered the original report."""
    n_threads = 8
    per_thread = SOAK_ITERS // n_threads
    budget = RSS_BUDGET * 2  # per-thread allocator arenas
    errors = []

    def run(iters, prefix):
        def worker(tid):
            try:
                for i in range(iters):
                    churn_once(make_node, new_collection, f"{prefix}-{tid}-{i}")
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=300)
        assert not any(t.is_alive() for t in threads), "soak threads did not finish"
        gc.collect()

    run(WARMUP_ITERS // n_threads, "warmup")

    baseline_peak = peak_rss_bytes()
    baseline_objs = vs.graph_object_count()

    run(per_thread, "soak")

    assert not errors, f"errors during concurrent soak: {errors[:3]}"

    growth = peak_rss_bytes() - baseline_peak
    leaked = vs.graph_object_count() - baseline_objs
    total = n_threads * per_thread * OBJECTS_PER_ITER

    assert growth < budget, (
        f"peak RSS grew {growth / MB:.1f} MB over {total} objects across "
        f"{n_threads} threads; budget is {budget / MB:.0f} MB")
    assert leaked < 100, f"registry grew by {leaked} entries during the soak"

    assert vs.is_running() and vs._background_thread.is_alive(), \
        "reaper thread died during the soak -- the original failure mode"


def test_rss_returns_to_baseline_after_churn(vs, make_node, new_collection):
    """Current (not peak) RSS should fall back near baseline once work is dropped.

    Catches a leak that peak-RSS can miss. Skipped where current RSS isn't
    readable without extra dependencies.
    """
    if current_rss_bytes() is None:
        pytest.skip("current RSS unavailable (needs Linux /proc or psutil)")

    run_churn(make_node, new_collection, WARMUP_ITERS, "retwarm")
    baseline = current_rss_bytes()

    run_churn(make_node, new_collection, SOAK_ITERS, "retained")

    growth = current_rss_bytes() - baseline
    assert growth < RSS_BUDGET, (
        f"RSS stayed {growth / MB:.1f} MB above baseline after dropping all work")
