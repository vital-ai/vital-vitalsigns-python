import hashlib
import json
import logging
import os
import tempfile
import time
from importlib.metadata import entry_points, distribution, PackageNotFoundError
from pathlib import Path
from typing import Optional, Dict, Any


PROP_CLASS_NAME_MAP = {
    "BooleanProperty": "vital_ai_vitalsigns.model.properties.BooleanProperty.BooleanProperty",
    "StringProperty": "vital_ai_vitalsigns.model.properties.StringProperty.StringProperty",
    "IntegerProperty": "vital_ai_vitalsigns.model.properties.IntegerProperty.IntegerProperty",
    "DoubleProperty": "vital_ai_vitalsigns.model.properties.DoubleProperty.DoubleProperty",
    "DateTimeProperty": "vital_ai_vitalsigns.model.properties.DateTimeProperty.DateTimeProperty",
    "GeoLocationProperty": "vital_ai_vitalsigns.model.properties.GeoLocationProperty.GeoLocationProperty",
    "TruthProperty": "vital_ai_vitalsigns.model.properties.TruthProperty.TruthProperty",
    "URIProperty": "vital_ai_vitalsigns.model.properties.URIProperty.URIProperty",
}

CACHE_VERSION = 1


class VitalSignsRegistryCache:

    @staticmethod
    def get_cache_path() -> Path:
        package_dir = Path(__file__).parent.parent
        cache_dir = package_dir / "_vitalsigns_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / "registry_cache.json"

    @staticmethod
    def compute_cache_key() -> str:
        package_info = []
        for ep in entry_points(group='vitalsigns_packages'):
            try:
                dist_name = ep.dist.name if ep.dist else ep.value.split('.')[0]
                dist_obj = distribution(dist_name)
                version = dist_obj.version
            except (PackageNotFoundError, AttributeError):
                version = "unknown"
            package_info.append((ep.name, ep.value, version))

        package_info.sort()

        key_string = json.dumps(package_info, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    @staticmethod
    def load_cache(cache_path: Path, cache_key: str) -> Optional[Dict[str, Any]]:
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            if cached.get('cache_version') != CACHE_VERSION:
                logging.info("Registry cache version mismatch, will rescan.")
                return None

            if cached.get('cache_key') != cache_key:
                logging.info("Registry cache key mismatch (packages changed), will rescan.")
                return None

            logging.info("Registry cache hit — loading from cache.")
            return cached

        except (json.JSONDecodeError, KeyError, IOError) as e:
            logging.warning(f"Failed to load registry cache: {e}")
            return None

    @staticmethod
    def save_cache(cache_path: Path, cache_key: str, data: Dict[str, Any]):
        data['cache_key'] = cache_key
        data['cache_version'] = CACHE_VERSION
        data['timestamp'] = time.time()

        # Written atomically: open(path, 'w') truncates immediately and fills
        # incrementally, so a concurrent reader (another worker process starting
        # at the same time) could see truncated JSON, and two concurrent writers
        # could interleave into corruption. Write to a unique temp file in the
        # same directory, then os.replace(), which is atomic on POSIX and
        # Windows -- a torn write leaves the previous good cache intact.
        tmp_path = None
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                dir=str(cache_path.parent),
                prefix=f".{cache_path.name}.",
                suffix=".tmp")
            tmp_path = Path(tmp_name)
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, cache_path)
            tmp_path = None
            logging.info(f"Registry cache saved to {cache_path}")
        except (IOError, OSError) as e:
            logging.warning(f"Failed to save registry cache: {e}")
        finally:
            if tmp_path is not None:
                # never leave a partial temp file behind
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def serialize_registry(vitalsigns_classes: dict,
                           vitalsigns_property_classes: dict,
                           domain_property_map: dict,
                           range_property_map: dict,
                           ont_tuple_list: list,
                           ont_iri_list: list) -> Dict[str, Any]:

        def _path(entry):
            # entry may already be a dotted path (restored from a cache) or a
            # real class (fresh scan). Never force a lazy map to resolve just
            # to write it back out.
            if isinstance(entry, str):
                return entry
            return f"{entry.__module__}.{entry.__qualname__}"

        def _raw(mapping):
            return mapping.raw_items() if hasattr(mapping, 'raw_items') else mapping.items()

        classes_cache = {uri: _path(cls) for uri, cls in _raw(vitalsigns_classes)}
        properties_cache = {uri: _path(cls) for uri, cls in _raw(vitalsigns_property_classes)}

        domain_prop_cache = {}
        for class_uri, class_map in domain_property_map.items():
            domain_prop_cache[class_uri] = list(class_map["prop_set"])

        range_prop_cache = {}
        for prop_uri, prop_info in range_property_map.items():
            entry = {
                "property_uri": prop_info["property_uri"],
                "property_type": prop_info["property_type"],
            }
            if "data_type" in prop_info:
                entry["data_type"] = prop_info["data_type"]
            if "range_class_list" in prop_info:
                entry["range_class_list"] = [str(c) for c in prop_info["range_class_list"]]

            prop_class = prop_info.get("prop_class")
            if prop_class is not None:
                entry["prop_class_name"] = prop_class.__name__
            else:
                entry["prop_class_name"] = None

            range_prop_cache[prop_uri] = entry

        return {
            "vitalsigns_classes": classes_cache,
            "vitalsigns_property_classes": properties_cache,
            "domain_property_map": domain_prop_cache,
            "range_property_map": range_prop_cache,
            "ont_tuple_list": ont_tuple_list,
            "ont_iri_list": ont_iri_list,
        }

    @staticmethod
    def deserialize_prop_class(prop_class_name: Optional[str]):
        if prop_class_name is None:
            return None

        import_path = PROP_CLASS_NAME_MAP.get(prop_class_name)
        if import_path is None:
            logging.warning(f"Unknown property class name in cache: {prop_class_name}")
            return None

        module_path, class_name = import_path.rsplit('.', 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @staticmethod
    def deserialize_domain_property_map(cached_map: dict) -> dict:
        result = {}
        for class_uri, prop_list in cached_map.items():
            result[class_uri] = {"prop_set": set(prop_list)}
        return result

    @staticmethod
    def deserialize_range_property_map(cached_map: dict) -> dict:
        from rdflib import URIRef

        result = {}
        for prop_uri, entry in cached_map.items():
            prop_info = {
                "property_uri": entry["property_uri"],
                "property_type": entry["property_type"],
            }
            if "data_type" in entry:
                prop_info["data_type"] = entry["data_type"]
            if "range_class_list" in entry:
                prop_info["range_class_list"] = [URIRef(c) for c in entry["range_class_list"]]

            prop_info["prop_class"] = VitalSignsRegistryCache.deserialize_prop_class(
                entry.get("prop_class_name")
            )

            result[prop_uri] = prop_info
        return result
