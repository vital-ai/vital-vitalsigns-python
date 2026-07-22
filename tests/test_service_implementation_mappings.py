"""Implementation mappings must name classes that actually exist.

`vitalsigns_config.yaml` maps a database type to a dotted class path, which
ServiceFactory imports at startup. Nothing validated those paths, so they rotted
silently: of 12 mappings, only ONE resolved.

  - `weaviate` pointed at vital_ai_vitalsigns.service.vector.weaviate.
    weaviate_service.WeaviateVectorService. That module was deleted in 515a9a1
    (2025-10-16), the same commit that commented out the weaviate-client
    dependency and added qdrant-client. The config was never updated.
  - `fuseki_memory`, `rdflib_memory`, `pyoxigraph_memory` and `qdrant_memory`
    named classes via package paths whose __init__.py files are empty, so the
    classes were not importable there (and two of them do not exist at all).

All four configured services requested `weaviate`, so every one of them failed
to construct on every startup -- and VitalServiceManager logs and continues, so
a deployment with zero working services looked healthy. The failure went
unnoticed for months.

External `vitalservice_*` packages are optional plugins and legitimately absent,
so assertions here are scoped to in-tree (`vital_ai_vitalsigns.*`) paths.
"""

import importlib
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = (REPO_ROOT / "vitalhome" / "vital-config" / "vitalsigns"
               / "vitalsigns_config.yaml")

INTREE_PREFIX = "vital_ai_vitalsigns."


def resolve(dotted_path):
    """Import the class a mapping names; raises if it cannot be resolved."""
    module_path, _, class_name = dotted_path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def load_mappings():
    if not CONFIG_PATH.exists():
        pytest.skip(f"no config file at {CONFIG_PATH} (it is gitignored)")
    config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    mapping = (config.get("vitalservice") or {}).get("implementation_mapping") or {}
    if not mapping:
        pytest.skip("config has no implementation_mapping section")
    return mapping


# --------------------------------------------------------------------------
# CI-safe: these run everywhere, with or without a config file
# --------------------------------------------------------------------------

class TestInTreeClassesExistWhereConfigExpects:
    """Pins the canonical paths the config maps to. Runs without a config file,
    so CI catches a move or rename even on a fresh clone."""

    @pytest.mark.parametrize("dotted_path", [
        "vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service.VirtuosoGraphService",
        "vital_ai_vitalsigns.service.graph.memory.memory_graph_service.MemoryGraphService",
        "vital_ai_vitalsigns.service.vector.memory.memory_service.VectorMemoryService",
    ])
    def test_class_is_importable(self, dotted_path):
        assert resolve(dotted_path) is not None

    def test_deleted_weaviate_module_is_really_gone(self):
        """Documents the 515a9a1 removal. If someone restores the module, the
        mapping can come back -- until then it must not be re-added to config."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(
                "vital_ai_vitalsigns.service.vector.weaviate.weaviate_service")

    def test_empty_package_inits_do_not_re_export(self):
        """Why the mappings broke: the package __init__ files are empty, so
        `package.ClassName` does not resolve -- the module must be named."""
        for package, class_name in [
            ("vital_ai_vitalsigns.service.graph.memory", "MemoryGraphService"),
            ("vital_ai_vitalsigns.service.vector.memory", "VectorMemoryService"),
        ]:
            module = importlib.import_module(package)
            assert not hasattr(module, class_name), (
                f"{package} now re-exports {class_name}; the config may use the "
                f"shorter path, but this test's premise has changed")


# --------------------------------------------------------------------------
# Config-driven: skipped when the (gitignored) config file is absent
# --------------------------------------------------------------------------

class TestConfiguredMappings:

    def test_every_intree_mapping_resolves(self):
        """The guard that would have caught this. External plugins are exempt."""
        failures = {}
        for kind in ("graph_databases", "vector_databases"):
            for name, path in (load_mappings().get(kind) or {}).items():
                if not path.startswith(INTREE_PREFIX):
                    continue
                try:
                    resolve(path)
                except Exception as e:
                    failures[f"{kind}.{name}"] = f"{type(e).__name__}: {e}"

        assert failures == {}, (
            f"config maps database types to classes that cannot be imported: {failures}")

    def test_external_mappings_are_plausibly_named(self):
        """Out-of-tree plugins can't be imported here, but a typo'd path is
        still worth catching: they must be dotted paths, not bare names."""
        offenders = {}
        for kind in ("graph_databases", "vector_databases"):
            for name, path in (load_mappings().get(kind) or {}).items():
                if path.startswith(INTREE_PREFIX):
                    continue
                if "." not in path or not path.rpartition(".")[2][:1].isupper():
                    offenders[f"{kind}.{name}"] = path

        assert offenders == {}, f"malformed implementation paths: {offenders}"

    def test_every_service_requests_a_mapped_database_type(self):
        """A service naming an unmapped type raises ValueError in ServiceFactory
        and takes the whole service down."""
        if not CONFIG_PATH.exists():
            pytest.skip("no config file")
        config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        section = config.get("vitalservice") or {}
        mapping = section.get("implementation_mapping") or {}
        graph_types = set(mapping.get("graph_databases") or {})
        vector_types = set(mapping.get("vector_databases") or {})

        unmapped = {}
        for service in section.get("services") or []:
            gdb = service.get("graph_database") or {}
            vdb = service.get("vector_database") or {}
            if gdb.get("database_type") and gdb["database_type"] not in graph_types:
                unmapped[f"{service.get('name')}.graph"] = gdb["database_type"]
            if vdb.get("vector_database_type") and \
                    vdb["vector_database_type"] not in vector_types:
                unmapped[f"{service.get('name')}.vector"] = vdb["vector_database_type"]

        assert unmapped == {}, (
            f"services request database types with no implementation mapping: {unmapped}")


class TestServicesActuallyConstruct:
    """The end symptom: services failing to build is logged and swallowed, so
    a zero-service deployment looks healthy. Assert they really come up."""

    def test_all_configured_services_construct(self, vs):
        if not CONFIG_PATH.exists():
            pytest.skip("no config file")

        config = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        configured = [s.get("name") for s in
                      ((config.get("vitalservice") or {}).get("services") or [])]
        if not configured:
            pytest.skip("config defines no services")

        manager = vs.get_vitalservice_manager()
        built = set(manager.get_vitalservice_list())

        missing = [name for name in configured if name not in built]
        assert missing == [], (
            f"{len(missing)} of {len(configured)} configured services failed to "
            f"construct: {missing}")

    def test_constructed_services_have_a_backing_store(self, vs):
        """A service with neither a graph nor a vector backend is inert."""
        manager = vs.get_vitalservice_manager()
        names = list(manager.get_vitalservice_list())
        if not names:
            pytest.skip("no services configured")

        inert = [n for n in names
                 if not manager.get_vitalservice(n).is_graph_service()
                 and not manager.get_vitalservice(n).is_vector_service()]
        assert inert == [], f"services with no backing store: {inert}"
