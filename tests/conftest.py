import os
import sys

import pytest

# Tests import the working tree, not any installed copy of the package.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture(scope="session")
def vs():
    """The VitalSigns singleton, with its background thread running.

    Session-scoped because VitalSigns is a process singleton whose construction
    is expensive (ontology load + registry build) and cannot be repeated.
    """
    from vital_ai_vitalsigns.vitalsigns import VitalSigns

    instance = VitalSigns()
    if not instance.is_running():
        instance.start()
    yield instance
    instance.stop()


@pytest.fixture
def registry_enabled(vs):
    """Turn the (default-off) object registry on for the duration of a test.

    The registry is opt-in, so tests that assert on graph_object_count must
    enable it explicitly. Restores the previous setting afterwards.
    """
    previous = vs.is_object_registry_enabled()
    vs.set_object_registry_enabled(True)
    yield vs
    vs.set_object_registry_enabled(previous)


@pytest.fixture
def new_collection():
    """Factory for GraphCollections without the rdfstore/vectordb side services."""
    from vital_ai_vitalsigns.collection.graph_collection import GraphCollection

    def _make(**kwargs):
        kwargs.setdefault("use_rdfstore", False)
        kwargs.setdefault("use_vectordb", False)
        return GraphCollection(**kwargs)

    return _make


@pytest.fixture
def make_node():
    """Factory for uniquely-URI'd VITAL_Node instances."""
    from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node

    def _make(suffix):
        node = VITAL_Node()
        node.URI = f"urn:vitalsigns-test:{suffix}"
        node.name = f"node-{suffix}"
        return node

    return _make
