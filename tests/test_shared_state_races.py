"""Race tests for shared mutable state (C5, C6).

C5 -- RDFlibSparqlImpl created self.lock and used it in exactly one of four
      methods that mutate the shared rdflib Dataset. Latent rather than
      demonstrated: see TestRdflibImplLocking's docstring for what these tests
      do and do not prove.

C6 -- The registry cache was written with open(path, 'w') + json.dump, which
      truncates immediately and fills incrementally. A concurrent reader could
      see truncated JSON; concurrent writers could interleave into corruption.
      Measured against the original implementation, readers observed 150 torn
      states in a single run -- this one is demonstrated, not theoretical.
"""

import json
import multiprocessing
import sys
import threading
from pathlib import Path

import pytest

from vital_ai_vitalsigns.impl.rdflib.rdflib_sparql_impl import RDFlibSparqlImpl
from vital_ai_vitalsigns.impl.vitalsigns_registry_cache import (
    CACHE_VERSION,
    VitalSignsRegistryCache,
)


@pytest.fixture
def fast_switching():
    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    yield
    sys.setswitchinterval(previous)


# --------------------------------------------------------------------------
# C5 -- RDFlibSparqlImpl
# --------------------------------------------------------------------------

class TestRdflibImplLocking:
    """Note on what these prove.

    The *structural* test below is the real guard for C5. The two behavioural
    tests were measured against the unlocked implementation and it passed them:
    rdflib's default in-memory store is dict-backed, so under the GIL these
    particular operations happen to survive without the lock. They are therefore
    smoke/regression tests, not evidence of the bug.

    The fix is still correct: rdflib documents no thread-safety guarantee, its
    stores are pluggable (a SQLite/Berkeley-backed store has entirely different
    behaviour), and the class already claimed synchronization by holding the
    lock in _insert_object_list_impl. Partial lock coverage is a latent defect
    whether or not today's store tolerates it.
    """

    def test_all_graph_mutators_hold_the_lock(self):
        """Structural check -- the primary guard for C5.

        The bug was a lock used in 1 of 4 mutators, which reads as 'this class
        is synchronized' while three methods race. This test fails immediately
        if a mutator loses its guard again.
        """
        import inspect

        source = inspect.getsource(RDFlibSparqlImpl)
        for name in ("_create_graph_impl", "_delete_graph_impl", "_purge_graph_impl"):
            method = getattr(RDFlibSparqlImpl, name)
            body = inspect.getsource(method)
            assert "with self.lock" in body, (
                f"{name} mutates the shared rdflib graph without holding self.lock")

        assert "with self.lock" in source

    def test_lock_is_reentrant(self):
        """These methods call one another (import -> purge), so a plain Lock
        would self-deadlock."""
        impl = RDFlibSparqlImpl(multigraph=True)
        with impl.lock:
            with impl.lock:
                pass  # a non-reentrant Lock would hang here

    def test_concurrent_create_delete_does_not_corrupt(self, fast_switching):
        """Smoke test (see class docstring -- passes unlocked too).

        Hammers structural mutations from many threads; rdflib must not raise
        and the dataset must stay usable.
        """
        impl = RDFlibSparqlImpl(multigraph=True)
        errors = []

        def churn(tid):
            try:
                for i in range(30):
                    uri = f"http://example.com/graph/{tid}-{i}"
                    impl._create_graph_impl(graph_uri=uri, enforce_segment=False)
                    impl._delete_graph_impl(graph_uri=uri, enforce_segment=False)
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=churn, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)

        assert not any(t.is_alive() for t in threads), "churn threads did not finish"
        assert not errors, f"errors during concurrent graph mutation: {errors[:3]}"

        # the dataset must still be walkable
        assert impl._list_graphs_impl() is not None

    def test_concurrent_create_across_shared_instance(self, fast_switching):
        """Smoke test (see class docstring -- passes unlocked too).

        Many threads creating distinct graphs on one instance: every graph must
        survive. A lost update would mean the mutation raced.
        """
        impl = RDFlibSparqlImpl(multigraph=True)
        n_threads, per_thread = 8, 20
        errors = []

        def create(tid):
            try:
                for i in range(per_thread):
                    impl._create_graph_impl(
                        graph_uri=f"http://example.com/keep/{tid}-{i}",
                        enforce_segment=False)
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=create, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)

        assert not errors, f"errors during concurrent create: {errors[:3]}"

        identifiers = {str(g.identifier) for g in impl.graph.graphs()}
        expected = {f"http://example.com/keep/{t}-{i}"
                    for t in range(n_threads) for i in range(per_thread)}
        missing = expected - identifiers
        assert not missing, f"{len(missing)} graphs lost to a race, e.g. {sorted(missing)[:3]}"


# --------------------------------------------------------------------------
# C6 -- registry cache atomic write
# --------------------------------------------------------------------------

def _sample_payload(n=200):
    return {"classes": {f"http://example.com/c/{i}": f"mod.Class{i}" for i in range(n)}}


def _write_cache(args):
    """Module-level for picklability under multiprocessing."""
    path_str, key, n = args
    from vital_ai_vitalsigns.impl.vitalsigns_registry_cache import VitalSignsRegistryCache
    VitalSignsRegistryCache.save_cache(Path(path_str), key, _sample_payload(n))
    return True


class TestRegistryCacheAtomicWrite:

    def test_roundtrip(self, tmp_path):
        cache_path = tmp_path / "registry_cache.json"
        VitalSignsRegistryCache.save_cache(cache_path, "key-1", _sample_payload())

        loaded = VitalSignsRegistryCache.load_cache(cache_path, "key-1")
        assert loaded is not None
        assert loaded["cache_version"] == CACHE_VERSION
        assert loaded["cache_key"] == "key-1"
        assert len(loaded["classes"]) == 200

    def test_no_temp_files_left_behind(self, tmp_path):
        cache_path = tmp_path / "registry_cache.json"
        VitalSignsRegistryCache.save_cache(cache_path, "key-1", _sample_payload())

        leftovers = [p.name for p in tmp_path.iterdir() if p.name != cache_path.name]
        assert leftovers == [], f"temp files left behind: {leftovers}"

    def test_concurrent_readers_never_see_a_torn_file(self, tmp_path, fast_switching):
        """The core guarantee: a reader either sees the old cache or the new
        one, never a truncated prefix. With open('w') the file is empty from
        truncation until the dump completes."""
        cache_path = tmp_path / "registry_cache.json"
        VitalSignsRegistryCache.save_cache(cache_path, "key-0", _sample_payload())

        stop = threading.Event()
        torn = []
        errors = []

        def reader():
            try:
                while not stop.is_set():
                    if not cache_path.exists():
                        torn.append("missing")
                        continue
                    try:
                        with open(cache_path) as fh:
                            json.load(fh)
                    except json.JSONDecodeError:
                        torn.append("truncated")
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        def writer():
            try:
                for i in range(60):
                    VitalSignsRegistryCache.save_cache(
                        cache_path, f"key-{i}", _sample_payload())
            except BaseException as e:  # noqa: BLE001
                errors.append(e)

        readers = [threading.Thread(target=reader) for _ in range(4)]
        writers = [threading.Thread(target=writer) for _ in range(3)]
        for t in readers + writers:
            t.start()
        for t in writers:
            t.join(timeout=120)
        stop.set()
        for t in readers:
            t.join(timeout=30)

        assert not errors, f"unexpected errors: {errors[:3]}"
        assert torn == [], (
            f"readers observed {len(torn)} torn/missing cache states "
            f"({torn[:5]}) -- the write is not atomic")

    def test_concurrent_writer_processes_leave_a_valid_cache(self, tmp_path):
        """The real-world trigger: N worker processes cold-starting together,
        all missing the cache and all writing it."""
        cache_path = tmp_path / "registry_cache.json"
        n_procs = 6

        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(n_procs) as pool:
            results = pool.map(
                _write_cache,
                [(str(cache_path), f"key-{i}", 200 + i) for i in range(n_procs)])

        assert all(results)
        assert cache_path.exists()

        with open(cache_path) as fh:
            data = json.load(fh)  # must parse: one writer won cleanly
        assert data["cache_version"] == CACHE_VERSION
        assert data["cache_key"].startswith("key-")

        leftovers = [p.name for p in tmp_path.iterdir() if p.name != cache_path.name]
        assert leftovers == [], f"temp files left behind by concurrent writers: {leftovers}"

    def test_failed_write_preserves_previous_cache(self, tmp_path, monkeypatch):
        """A torn write must leave the last good cache intact rather than an
        empty file, which is what open('w') produced on any mid-write failure."""
        cache_path = tmp_path / "registry_cache.json"
        VitalSignsRegistryCache.save_cache(cache_path, "good-key", _sample_payload())
        original = cache_path.read_text()

        def exploding_dump(*args, **kwargs):
            raise IOError("simulated disk failure mid-write")

        monkeypatch.setattr(json, "dump", exploding_dump)
        VitalSignsRegistryCache.save_cache(cache_path, "bad-key", _sample_payload())
        monkeypatch.undo()

        assert cache_path.read_text() == original, "a failed write clobbered the good cache"
        loaded = VitalSignsRegistryCache.load_cache(cache_path, "good-key")
        assert loaded is not None and loaded["cache_key"] == "good-key"

        leftovers = [p.name for p in tmp_path.iterdir() if p.name != cache_path.name]
        assert leftovers == [], f"failed write left temp files: {leftovers}"
