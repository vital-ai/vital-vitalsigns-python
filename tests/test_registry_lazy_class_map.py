"""The registry must always hand back classes, warm cache or cold.

`VitalSignsRegistry.vitalsigns_classes` is annotated Dict[str, Type[GraphObject]]
and held real classes until the registry cache was introduced. The cache stores
importable paths so a hit avoids importing thousands of modules, and after a
cache load the dict held those raw strings instead. The value type therefore
depended on whether the cache happened to be warm.

Callers iterating .values() got strings:

    'str' object has no attribute '__name__'         (script_domain_test.py)
    'str' object has no attribute '__module__'       (script_ontology_manager.py)
    'str' object has no attribute 'multiple_values'  (jsonld/test_rdf_debug.py)

LazyClassMap restores the contract -- reads resolve -- while keeping storage
lazy. See planning/issues/non-pytest-script-run.md.
"""

import inspect

import pytest

from vital_ai_vitalsigns.impl.vitalsigns_registry import LazyClassMap

VITAL_NODE_URI = "http://vital.ai/ontology/vital-core#VITAL_Node"
NODE_PATH = "vital_ai_vitalsigns.model.VITAL_Node.VITAL_Node"


class TestLazyClassMapUnit:
    """Exercised directly, so these run regardless of cache state."""

    def test_string_entry_resolves_to_a_class_on_read(self):
        m = LazyClassMap({})
        m["u"] = NODE_PATH

        assert inspect.isclass(m["u"])
        assert m["u"].__name__ == "VITAL_Node"

    def test_class_entry_passes_through(self):
        from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
        m = LazyClassMap({})
        m["u"] = VITAL_Node
        assert m["u"] is VITAL_Node

    def test_values_and_items_resolve(self):
        m = LazyClassMap({})
        m["u"] = NODE_PATH

        assert all(inspect.isclass(v) for v in m.values())
        assert all(inspect.isclass(v) for _, v in m.items())

    def test_resolution_is_lazy_then_memoized(self):
        resolved = {}
        m = LazyClassMap(resolved)
        m["u"] = NODE_PATH

        assert resolved == {}, "resolved eagerly on assignment"
        m["u"]
        assert list(resolved) == ["u"], "not memoized after first read"

    def test_shares_the_registry_resolution_cache(self):
        """The map and get_vitalsigns_class() must not resolve independently."""
        resolved = {}
        m = LazyClassMap(resolved)
        m["u"] = NODE_PATH
        cls = m["u"]
        assert resolved["u"] is cls

    def test_missing_key_raises_keyerror_like_a_dict(self):
        m = LazyClassMap({})
        with pytest.raises(KeyError):
            m["nope"]
        assert m.get("nope") is None
        assert m.get("nope", "dflt") == "dflt"

    def test_overwrite_drops_the_stale_resolution(self):
        from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
        resolved = {}
        m = LazyClassMap(resolved)
        m["u"] = NODE_PATH
        assert m["u"].__name__ == "VITAL_Node"

        m["u"] = VITAL_Edge
        assert m["u"] is VITAL_Edge, "returned the previously resolved class"

    def test_delete_drops_the_resolution(self):
        resolved = {}
        m = LazyClassMap(resolved)
        m["u"] = NODE_PATH
        m["u"]
        del m["u"]
        assert "u" not in m and "u" not in resolved

    def test_len_contains_iter_behave_like_a_dict(self):
        m = LazyClassMap({})
        m["a"] = NODE_PATH
        m["b"] = NODE_PATH
        assert len(m) == 2 and "a" in m and sorted(m) == ["a", "b"]

    def test_update_works(self):
        m = LazyClassMap({})
        m.update({"a": NODE_PATH, "b": NODE_PATH})
        assert len(m) == 2 and inspect.isclass(m["a"])

    def test_raw_items_does_not_resolve(self):
        """The cache serializer must not force the whole registry to import."""
        resolved = {}
        m = LazyClassMap(resolved)
        m["u"] = NODE_PATH

        raw = dict(m.raw_items())
        assert raw["u"] == NODE_PATH, "raw_items resolved the entry"
        assert resolved == {}, "raw_items triggered resolution"

    def test_replace_raw_clears_prior_resolutions(self):
        resolved = {}
        m = LazyClassMap(resolved)
        m["old"] = NODE_PATH
        m["old"]
        m.replace_raw({"new": NODE_PATH})

        assert "old" not in m and resolved == {}
        assert inspect.isclass(m["new"])


class TestLiveRegistry:
    """The real registry, whichever path it loaded by."""

    def test_class_values_are_classes(self, vs):
        reg = vs.get_registry()
        strings = [v for v in reg.vitalsigns_classes.values() if isinstance(v, str)]
        assert strings == [], (
            f"{len(strings)} registry entries are raw path strings, not classes")

    def test_property_class_values_are_classes(self, vs):
        reg = vs.get_registry()
        strings = [v for v in reg.vitalsigns_property_classes.values() if isinstance(v, str)]
        assert strings == [], (
            f"{len(strings)} property entries are raw path strings, not classes")

    def test_indexing_matches_the_accessor(self, vs):
        reg = vs.get_registry()
        assert reg.vitalsigns_classes[VITAL_NODE_URI] is reg.get_vitalsigns_class(VITAL_NODE_URI)

    def test_class_attributes_are_usable(self, vs):
        """The exact operations the failing scripts performed."""
        reg = vs.get_registry()
        cls = reg.vitalsigns_classes[VITAL_NODE_URI]
        assert cls.__name__ == "VITAL_Node"
        assert cls.__module__.startswith("vital_ai_vitalsigns")

    def test_cache_hit_does_not_resolve_everything_up_front(self):
        """Laziness is the reason the cache exists; resolving all ~1800 classes
        on load would undo it.

        Runs in a subprocess: the session-scoped `vs` fixture is shared, and any
        earlier test that touches .values() resolves the whole registry, so an
        in-process check measures test order rather than load behaviour.
        """
        import pathlib
        import subprocess
        import sys

        repo = pathlib.Path(__file__).resolve().parent.parent
        code = (
            "import logging; logging.disable(logging.CRITICAL)\n"
            "from vital_ai_vitalsigns.vitalsigns import VitalSigns\n"
            "r = VitalSigns().get_registry()\n"
            "print(r._loaded_from_cache, len(r._resolved_classes), len(r.vitalsigns_classes))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=str(repo), capture_output=True,
            text=True, timeout=600,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(repo),
                 "HOME": str(pathlib.Path.home())},
        )
        assert result.returncode == 0, f"subprocess failed: {result.stderr[-1500:]}"

        from_cache, resolved, total = result.stdout.strip().split()
        if from_cache != "True":
            pytest.skip("registry was built by a full scan, not a cache hit")

        assert int(resolved) == 0, (
            f"a cache hit eagerly resolved {resolved} of {total} classes; "
            f"the lazy import that makes the cache worthwhile is gone")
