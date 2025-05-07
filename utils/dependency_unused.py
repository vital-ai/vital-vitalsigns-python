import os
import ast
import importlib.metadata as metadata
from importlib.metadata import PackageNotFoundError
from packaging.requirements import Requirement


def extract_dependencies() -> list[str]:
    """Extract the `install_requires` list literal from setup.py."""
    setup_dir = os.path.join(os.path.dirname(__file__), '..')
    setup_path = os.path.join(setup_dir, 'setup.py')

    with open(setup_path, 'r') as f:
        setup_code = f.read()

    setup_ast = ast.parse(setup_code)
    install_requires: list[str] = []

    for node in ast.walk(setup_ast):
        if (
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and
            node.func.id == 'setup'
        ):
            for kw in node.keywords:
                if kw.arg == 'install_requires' and isinstance(kw.value, ast.List):
                    install_requires = [elt.s for elt in kw.value.elts if isinstance(elt, ast.Constant)]
            break

    return install_requires  # type: ignore[list-item]


def get_all_dependencies(package_names: list[str]) -> set[str]:
    """
    Recursively gather all dependencies (and their dependencies)
    for the given list of distribution names.
    """
    all_deps: set[str] = set()
    to_check: set[str] = set(package_names)

    while to_check:
        pkg = to_check.pop()
        if pkg in all_deps:
            continue
        all_deps.add(pkg)
        try:
            req_specs = metadata.requires(pkg) or []
            # Parse specifiers into package names
            deps = {Requirement(spec).name for spec in req_specs}
            to_check.update(deps)
        except PackageNotFoundError:
            print(f"Warning: distribution not found: {pkg}")

    return all_deps


def get_installed_packages() -> set[str]:
    """
    Return the set of all installed distribution names
    in the current environment.
    """
    return {dist.name for dist in metadata.distributions()}


def main():
    # 1. Read direct dependencies from setup.py
    direct = extract_dependencies()
    # 2. Expand to all transitive dependencies
    required = get_all_dependencies([Requirement(d).name for d in direct])
    # 3. Compare against installed packages
    installed = get_installed_packages()
    unused = installed - required

    if unused:
        print("Unused libraries:")
        for pkg in sorted(unused):
            print(f"  - {pkg}")
    else:
        print("No unused libraries found.")


if __name__ == "__main__":
    main()

