"""The library logs; it does not print, and it does not configure logging.

Two related problems motivated this:

  - 55 print() calls across 10 modules wrote to stdout. In a container that is
    invisible to log aggregation, unfilterable, and unsuppressable -- a
    completely broken service config looked identical to a healthy one, because
    "Warning: Failed to create service ..." went to stdout rather than a log
    record with a level and a logger name.

  - vitalsigns_config.yaml carried a `vitalsigns.logging.level` key that nothing
    read. It was dead configuration that looked functional.

The resolution: per-module `logging.getLogger(__name__)` everywhere, and the
library never configures logging -- level and handler setup belong to the host
application. The dead config key was removed rather than implemented.
"""

import ast
import logging
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "vital_ai_vitalsigns"


def library_python_files():
    return sorted(p for p in PACKAGE_ROOT.rglob("*.py")
                  if "__pycache__" not in p.parts)


def print_calls(path):
    """Line numbers of bare print() calls, via AST rather than grep so that
    multi-line calls and 'print' inside strings/comments are handled."""
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:  # pragma: no cover
        return []
    return [node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"]


class TestNoPrints:

    def test_library_contains_no_print_calls(self):
        offenders = {}
        for path in library_python_files():
            lines = print_calls(path)
            if lines:
                offenders[str(path.relative_to(REPO_ROOT))] = lines

        assert offenders == {}, (
            "print() in library code writes to stdout, where it cannot be "
            f"levelled, filtered or captured by log aggregation: {offenders}")

    def test_every_module_that_logs_defines_its_own_logger(self):
        """A module using a logger it never defined would raise NameError only
        on the failure path -- exactly when it is least welcome."""
        offenders = []
        for path in library_python_files():
            source = path.read_text()
            if "logger." not in source:
                continue
            if "getLogger" not in source:
                offenders.append(str(path.relative_to(REPO_ROOT)))

        assert offenders == [], f"modules use `logger` without defining one: {offenders}"


class TestDoesNotConfigureLogging:
    """A library that sets levels or adds handlers fights the host app's setup."""

    def test_no_basic_config_or_set_level_in_library(self):
        offenders = {}
        for path in library_python_files():
            source = path.read_text()
            hits = [name for name in ("logging.basicConfig", ".setLevel(", ".addHandler(")
                    if name in source]
            if hits:
                offenders[str(path.relative_to(REPO_ROOT))] = hits

        assert offenders == {}, (
            "the library configures logging; level and handler setup belong to "
            f"the host application: {offenders}")

    def test_importing_and_constructing_writes_nothing_to_stdout(self):
        """The end-user symptom: a clean process must have a clean stdout."""
        code = (
            "from vital_ai_vitalsigns.vitalsigns import VitalSigns\n"
            "VitalSigns()\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "PYTHONPATH": str(REPO_ROOT),
                 "HOME": str(pathlib.Path.home())},
        )
        assert result.returncode == 0, f"construction failed: {result.stderr[-2000:]}"
        assert result.stdout == "", (
            f"library wrote to stdout during construction:\n{result.stdout[:2000]}")

    def test_service_failures_are_emitted_as_log_records(self, caplog):
        """Positive counterpart: the information moved to logging, it was not
        deleted. A failing stop() must produce a real WARNING record carrying
        the service name -- levelled, named, and routable."""
        from vital_ai_vitalsigns.service.vitalservice_manager import VitalServiceManager

        class ExplodingService:
            def stop(self):
                raise RuntimeError("simulated stop failure")

        manager = VitalServiceManager()
        manager.services = {"doomed": ExplodingService()}
        manager.initialized = True

        with caplog.at_level(logging.WARNING,
                             logger="vital_ai_vitalsigns.service.vitalservice_manager"):
            manager.shutdown()

        records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert records, "the failure produced no log record at all"

        record = records[0]
        assert record.name == "vital_ai_vitalsigns.service.vitalservice_manager", (
            f"record came from {record.name}; it must carry the module's logger "
            f"name so it can be filtered and routed")
        assert "doomed" in record.getMessage()
        assert "simulated stop failure" in record.getMessage()


class TestLoggingConfigKeyRemoved:

    def test_logging_config_dataclass_is_gone(self):
        import vital_ai_vitalsigns.config.vitalsigns_config as cfg
        assert not hasattr(cfg, "LoggingConfig"), (
            "the vitalsigns.logging config key is back; it was removed because "
            "nothing applied it and the library should not configure logging")

    def test_a_stale_logging_key_is_ignored_not_fatal(self):
        """Existing deployments still have the key in their YAML. Parsing must
        tolerate it rather than blow up on an unknown field."""
        from vital_ai_vitalsigns.config.vitalsigns_config import VitalSignsConfigLoader

        config = VitalSignsConfigLoader.parse_yaml_config(
            "vitalsigns:\n"
            "  logging:\n"
            "    level: DEBUG\n"
            "vitalservice:\n"
            "  services: []\n"
        )
        assert config.vitalservice is not None
