"""GraphCollection.get() must find objects added after construction.

`_uri_map` — the index behind get() — was populated only in __init__. Neither
add() nor add_objects() wrote to it, so get() silently returned None for
anything added later while len() still counted the object. A lookup that
returns None instead of raising produces an AttributeError far from the cause;
that is exactly how it surfaced, as

    AttributeError: 'NoneType' object has no attribute 'name'

in test_scripts/script_graph_collection.py, ~35 lines after the real fault.

Found by running the non-pytest scripts; see
planning/issues/non-pytest-script-run.md.
"""

import pytest


@pytest.fixture
def node(vs, make_node):
    def _make(uri, name="Apple"):
        n = make_node(uri.replace(":", "-"))
        n.URI = uri
        n.name = name
        return n
    return _make


class TestLookupAfterAdd:

    def test_get_finds_object_added_with_add(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))

        found = c.get("uri:a")
        assert found is not None, "get() returned None for an object just add()ed"
        assert str(found.name) == "Apple"

    def test_get_finds_objects_added_with_add_objects(self, new_collection, node):
        c = new_collection()
        c.add_objects([node("uri:a"), node("uri:b"), node("uri:c")])

        for uri in ("uri:a", "uri:b", "uri:c"):
            assert c.get(uri) is not None, f"get({uri!r}) returned None after add_objects"

    def test_get_still_finds_constructor_supplied_objects(self, vs, node):
        """The one path that always worked -- must not regress."""
        from vital_ai_vitalsigns.collection.graph_collection import GraphCollection

        c = GraphCollection(data=[node("uri:ctor")], use_rdfstore=False, use_vectordb=False)
        assert c.get("uri:ctor") is not None

    def test_get_returns_default_for_absent_uri(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))

        assert c.get("uri:missing") is None
        assert c.get("uri:missing", "fallback") == "fallback"


class TestIndexStaysInStepWithData:
    """len() and get() must agree; a divergence is what made the bug invisible."""

    def test_index_size_matches_length_after_adds(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))
        c.add_objects([node("uri:b"), node("uri:c")])

        assert len(c._uri_map) == len(c) == 3

    def test_remove_clears_the_index(self, new_collection, node):
        c = new_collection()
        c.add_objects([node("uri:a"), node("uri:b")])

        c.remove("uri:a")

        assert c.get("uri:a") is None, "removed object still resolvable via get()"
        assert len(c._uri_map) == len(c) == 1

    def test_pop_clears_the_index(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))

        c.pop()

        assert c.get("uri:a") is None
        assert len(c._uri_map) == len(c) == 0

    def test_delitem_clears_the_index(self, new_collection, node):
        c = new_collection()
        c.add_objects([node("uri:a"), node("uri:b")])

        del c[0]

        assert len(c._uri_map) == len(c) == 1

    def test_readding_same_uri_replaces_rather_than_duplicates(self, new_collection, node):
        """add() calls pop_uri() first, so a repeat URI must update in place."""
        c = new_collection()
        c.add(node("uri:a", "Apple"))
        c.add(node("uri:a", "Banana"))

        assert len(c) == 1, "re-adding the same URI duplicated the entry"
        assert str(c.get("uri:a").name) == "Banana", "index kept the stale object"
        assert len(c._uri_map) == 1

    def test_insert_indexes_the_object(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))
        c.insert(0, node("uri:z"))

        assert c.get("uri:z") is not None
        assert len(c._uri_map) == len(c) == 2

    def test_setitem_reindexes(self, new_collection, node):
        c = new_collection()
        c.add(node("uri:a"))
        c[0] = node("uri:b")

        assert c.get("uri:b") is not None
        assert c.get("uri:a") is None, "replaced object still resolvable"
        assert len(c._uri_map) == len(c) == 1


def test_the_original_failing_script_scenario(new_collection, node):
    """Reproduces script_graph_collection.py, which failed with
    'NoneType' object has no attribute 'name' on the get() result."""
    c = new_collection()
    c.add_objects([node(f"uri:node{i}", f"name{i}") for i in range(1, 6)])

    found = c.get("uri:node2")
    assert found is not None
    assert str(found.name) == "name2"
