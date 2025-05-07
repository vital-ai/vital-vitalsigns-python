from importlib.metadata import distributions, requires, PackageNotFoundError
from packaging.requirements import Requirement


def find_leaf_packages() -> set[str]:
    """
    Return the set of installed package names that no other installed
    package depends on (i.e., "leaf" packages).
    """
    # Gather all installed distribution names
    all_pkgs = {dist.metadata['Name'].lower() for dist in distributions()}

    # Gather all declared dependencies
    deps: set[str] = set()
    for dist in distributions():
        pkg_name = dist.metadata['Name']
        try:
            req_specs = requires(pkg_name) or []
        except PackageNotFoundError:
            # Skip packages whose metadata can't be read
            continue
        for spec in req_specs:
            try:
                req = Requirement(spec)
            except Exception:
                continue
            deps.add(req.name.lower())

    # Leaf packages are those never listed as a dependency
    return all_pkgs - deps


def main():
    leaf_packages = find_leaf_packages()
    if leaf_packages:
        print("Packages that would be removed:")
        for pkg in sorted(leaf_packages):
            print(f"  - {pkg}")
    else:
        print("No packages would be removed.")


if __name__ == "__main__":
    main()
