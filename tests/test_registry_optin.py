"""Task C: the object registry is opt-in, default off.

The registry exists to support planned ontology inference over live objects
(rules like `person.age > 18 --> person.canDrive = true`), but that feature is
not in regular use. Until it is, every GraphObject construction should not pay
for it: with the registry off, __init__ does a single class-attribute test --
no import, no singleton lookup, no map write.
"""

import gc

import pytest

from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.vitalsigns import (
    OBJECT_REGISTRY_ENV_VAR,
    VitalSigns,
    _object_registry_default,
)


@pytest.fixture
def registry_off(vs):
    previous = vs.is_object_registry_enabled()
    vs.set_object_registry_enabled(False)
    yield vs
    vs.set_object_registry_enabled(previous)


class TestDefaultOff:

    def test_disabled_by_default_without_the_env_var(self, monkeypatch):
        monkeypatch.delenv(OBJECT_REGISTRY_ENV_VAR, raising=False)
        assert _object_registry_default() is False

    def test_objects_are_not_registered_when_off(self, registry_off, make_node):
        vs = registry_off
        before = vs.graph_object_count()

        held = [make_node(f"off-{i}") for i in range(50)]

        assert vs.graph_object_count() == before, (
            "objects were registered while the registry was disabled")
        assert len(held) == 50  # keep them alive so this isn't a GC artifact

    def test_include_graph_object_is_a_noop_when_off(self, registry_off, make_node):
        """Direct callers must be safe either way, not just __init__."""
        vs = registry_off
        node = make_node("direct")
        before = vs.graph_object_count()

        vs.include_graph_object(node)

        assert vs.graph_object_count() == before

    def test_graph_object_construction_skips_the_singleton_when_off(
            self, registry_off, monkeypatch):
        """The saving is the point: no import and no VitalSigns() lookup."""
        import vital_ai_vitalsigns.vitalsigns as vs_module
        from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node

        calls = []
        original = vs_module.VitalSignsMeta.__call__

        def counting_call(cls, *args, **kwargs):
            calls.append(1)
            return original(cls, *args, **kwargs)

        monkeypatch.setattr(vs_module.VitalSignsMeta, "__call__", counting_call)

        node = VITAL_Node()  # no properties set, so nothing else needs VitalSigns

        assert node is not None
        assert calls == [], (
            f"constructing a GraphObject hit the VitalSigns singleton "
            f"{len(calls)} time(s) with the registry disabled")


class TestEnabled:

    def test_objects_are_registered_when_on(self, registry_enabled, make_node):
        vs = registry_enabled
        before = vs.graph_object_count()

        held = [make_node(f"on-{i}") for i in range(50)]

        assert vs.graph_object_count() == before + 50
        assert len(held) == 50

    def test_still_self_evicts_when_on(self, registry_enabled, make_node):
        vs = registry_enabled
        before = vs.graph_object_count()

        node = make_node("evict-on")
        assert vs.graph_object_count() == before + 1

        del node
        gc.collect()
        assert vs.graph_object_count() == before

    def test_toggle_only_affects_later_objects(self, registry_off, make_node):
        """There is no backfill; the contract is 'from now on'."""
        vs = registry_off
        untracked = [make_node(f"before-{i}") for i in range(10)]
        before = vs.graph_object_count()

        vs.set_object_registry_enabled(True)
        try:
            tracked = [make_node(f"after-{i}") for i in range(10)]
            assert vs.graph_object_count() == before + 10, (
                "objects created before enabling should not be backfilled")
            assert len(tracked) == 10
        finally:
            vs.set_object_registry_enabled(False)
        assert len(untracked) == 10

    def test_flag_is_published_to_graphobject(self, vs):
        previous = vs.is_object_registry_enabled()
        try:
            vs.set_object_registry_enabled(True)
            assert GraphObject._registry_enabled is True
            vs.set_object_registry_enabled(False)
            assert GraphObject._registry_enabled is False
        finally:
            vs.set_object_registry_enabled(previous)


class TestEnvVar:

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " True "])
    def test_truthy_values_enable(self, monkeypatch, value):
        monkeypatch.setenv(OBJECT_REGISTRY_ENV_VAR, value)
        assert _object_registry_default() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "banana"])
    def test_other_values_do_not_enable(self, monkeypatch, value):
        monkeypatch.setenv(OBJECT_REGISTRY_ENV_VAR, value)
        assert _object_registry_default() is False


class TestPrecedence:
    """Most specific source wins: argument > env > off.

    The config file is deliberately NOT a source: vitalhome/**/*.yaml is
    gitignored, so a value set there does not travel with a deployment.
    """

    @staticmethod
    def resolve(argument, env, monkeypatch):
        if env is None:
            monkeypatch.delenv(OBJECT_REGISTRY_ENV_VAR, raising=False)
        else:
            monkeypatch.setenv(OBJECT_REGISTRY_ENV_VAR, env)
        return VitalSigns._resolve_object_registry(argument)

    def test_nothing_set_is_off(self, monkeypatch):
        assert self.resolve(None, None, monkeypatch) is False

    def test_env_only(self, monkeypatch):
        assert self.resolve(None, "true", monkeypatch) is True
        assert self.resolve(None, "false", monkeypatch) is False

    def test_argument_overrides_env(self, monkeypatch):
        assert self.resolve(True, "false", monkeypatch) is True
        assert self.resolve(False, "true", monkeypatch) is False

    def test_argument_false_is_respected_not_treated_as_unset(self, monkeypatch):
        """object_registry=False must mean off, not 'fall through to env'."""
        assert self.resolve(False, "true", monkeypatch) is False

    def test_config_file_is_not_consulted(self, monkeypatch):
        """A config carrying the old key must not switch the registry on."""
        from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfigLoader

        monkeypatch.delenv(OBJECT_REGISTRY_ENV_VAR, raising=False)

        config = VitalSignsConfigLoader.parse_yaml_config(
            "vitalsigns:\n  object_registry: true\n")
        assert not hasattr(config, "object_registry_enabled")
        assert VitalSigns._resolve_object_registry(None) is False

    def test_live_singleton_reflects_a_resolved_setting(self, vs):
        """End-to-end: whatever was resolved at construction is what the
        singleton and GraphObject agree on."""
        assert vs.is_object_registry_enabled() == GraphObject._registry_enabled


def test_collections_are_registered_regardless(vs, new_collection):
    """Only the object registry is opt-in. The collection map is small, bounded,
    and read by graph_collection_set(), so it stays always-on."""
    before = vs.graph_collection_count()
    held = new_collection()
    assert vs.graph_collection_count() == before + 1
    assert held is not None
