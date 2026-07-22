"""Task A: copy / deepcopy / pickle must work on GraphObjects.

Three independent defects broke them:

  A1  GraphObjectMeta.__getattr__ synthesized an AttributeComparisonProxy for
      EVERY unknown name, including dunders. Python's copy protocol probes with
      getattr(cls, "__copy__", None) and treats a truthy result as callable, so
      it got a non-callable proxy -> TypeError. The method previously carried a
      hand-maintained denylist of ~18 pydantic dunders to patch this for one
      library; raising for all dunders covers every consumer and the denylist
      is gone.

  A2  GraphObject.__getattr__ -> my_getattr reads self._properties, which
      __init__ installs. copy/pickle rebuild via cls.__new__(cls) WITHOUT
      __init__, so the read missed, landed back in __getattr__, and recursed
      until the stack blew.

  A3  Property classes are built dynamically inside
      VitalSignsImpl.create_property_with_trait_class, so they have no
      importable path and pickle could not reference them. GraphObject.__reduce__
      now round-trips through the library's own JSON form.

This matters for the deployment that prompted the whole investigation: LangGraph
checkpointing deep-copies and serializes state.
"""

import copy
import pickle

import pytest

from vital_ai_vitalsigns.model.GraphObject import GraphObject, GraphObjectMeta
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node


@pytest.fixture
def node(vs, make_node):
    n = make_node("protocols")
    n.rdfs_label = "a label"
    return n


# --------------------------------------------------------------------------
# A1 -- the metaclass must not synthesize dunders
# --------------------------------------------------------------------------

class TestMetaclassDunders:

    # Dunders genuinely absent from the MRO. Deliberately excludes ones that
    # really are defined -- __reduce_ex__/__getstate__ come from object,
    # __reduce__ is our own, and __get_pydantic_core_schema__ is implemented on
    # GraphObject. __getattr__ is only consulted after normal lookup fails, so
    # asserting on those would test nothing.
    DUNDERS = [
        "__copy__", "__deepcopy__", "__setstate__", "__iter__", "__len__",
        "__abstractmethods__", "__origin__", "__args__",
    ]

    @pytest.mark.parametrize("name", DUNDERS)
    def test_unknown_dunder_raises_attribute_error(self, vs, name):
        with pytest.raises(AttributeError):
            getattr(VITAL_Node, name)

    @pytest.mark.parametrize("name", DUNDERS)
    def test_hasattr_is_false_for_unknown_dunders(self, vs, name):
        assert not hasattr(VITAL_Node, name), (
            f"hasattr(VITAL_Node, {name!r}) is True; protocol probes will "
            f"receive a non-callable proxy")

    def test_query_dsl_proxy_still_works(self, vs):
        """The proxy is the point of __getattr__ -- don't regress it."""
        from vital_ai_vitalsigns.model.GraphObject import AttributeComparisonProxy
        assert isinstance(VITAL_Node.some_property_name, AttributeComparisonProxy)
        assert isinstance(VITAL_Node.age, AttributeComparisonProxy)

    def test_pydantic_denylist_is_gone(self):
        """The ~18-name denylist was a symptomatic patch; the general dunder
        rule replaces it. If it comes back, the root cause has regressed."""
        import inspect
        source = inspect.getsource(GraphObjectMeta.__getattr__)
        assert "__pydantic_core_schema__" not in source, (
            "the pydantic dunder denylist is back -- the general dunder rule "
            "should make it unnecessary")


# --------------------------------------------------------------------------
# A2 -- instance __getattr__ must not recurse on internal slots
# --------------------------------------------------------------------------

class TestInstanceInternalAttributes:

    def test_missing_internal_slot_raises_not_recurses(self, vs):
        """An object built without __init__ (as copy/pickle do) has no
        _properties. Reading it must raise, not recurse forever."""
        bare = VITAL_Node.__new__(VITAL_Node)
        with pytest.raises(AttributeError):
            bare._properties

    def test_missing_dunder_on_instance_raises(self, node):
        with pytest.raises(AttributeError):
            node.__some_missing_dunder__

    def test_normal_property_access_unaffected(self, node):
        assert str(node.name) == "node-protocols"
        assert str(node.rdfs_label) == "a label"

    def test_unknown_plain_attribute_still_raises(self, node):
        with pytest.raises(AttributeError):
            node.definitely_not_a_property_xyz


# --------------------------------------------------------------------------
# copy / deepcopy / pickle
# --------------------------------------------------------------------------

class TestCopyProtocols:

    def test_copy(self, node):
        clone = copy.copy(node)
        assert type(clone) is type(node)
        assert str(clone.URI) == str(node.URI)
        assert clone.to_json() == node.to_json()

    def test_deepcopy(self, node):
        clone = copy.deepcopy(node)
        assert type(clone) is type(node)
        assert str(clone.URI) == str(node.URI)
        assert clone.to_json() == node.to_json()

    def test_deepcopy_is_independent(self, node):
        clone = copy.deepcopy(node)
        clone.name = "changed"
        assert str(node.name) == "node-protocols", "deepcopy aliased the original"

    def test_deepcopy_of_a_container(self, vs, make_node):
        """The realistic shape: agent state holding a list/dict of objects."""
        state = {"nodes": [make_node(f"c-{i}") for i in range(3)]}
        clone = copy.deepcopy(state)

        assert len(clone["nodes"]) == 3
        assert [str(n.URI) for n in clone["nodes"]] == [str(n.URI) for n in state["nodes"]]

    def test_pickle_roundtrip(self, node):
        restored = pickle.loads(pickle.dumps(node))
        assert type(restored) is type(node)
        assert str(restored.URI) == str(node.URI)
        assert str(restored.name) == str(node.name)
        assert str(restored.rdfs_label) == str(node.rdfs_label)
        assert restored.to_json() == node.to_json()

    def test_pickle_roundtrip_of_a_container(self, vs, make_node):
        state = {"nodes": [make_node(f"p-{i}") for i in range(3)]}
        restored = pickle.loads(pickle.dumps(state))
        assert [str(n.URI) for n in restored["nodes"]] == [str(n.URI) for n in state["nodes"]]

    @pytest.mark.parametrize("protocol", [pickle.DEFAULT_PROTOCOL, pickle.HIGHEST_PROTOCOL])
    def test_pickle_across_protocols(self, node, protocol):
        restored = pickle.loads(pickle.dumps(node, protocol=protocol))
        assert restored.to_json() == node.to_json()

    def test_reduce_is_module_level_and_importable(self):
        """__reduce__ must name a module-level callable; a local function or
        bound method would itself be unpicklable."""
        from vital_ai_vitalsigns.model.GraphObject import _rebuild_graph_object_from_json
        assert _rebuild_graph_object_from_json.__module__ == \
            "vital_ai_vitalsigns.model.GraphObject"
