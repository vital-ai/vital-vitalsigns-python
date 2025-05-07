from importlib.metadata import distributions, requires, PackageNotFoundError
from packaging.requirements import Requirement


def find_dependents(package_name: str) -> list[str]:
    """
    Return a list of installed packages that declare a dependency
    on `package_name`.
    """
    dependents: list[str] = []

    for dist in distributions():
        # Get the canonical distribution name
        dist_name = dist.metadata.get('Name', dist.name)
        try:
            req_list = requires(dist_name) or []
        except PackageNotFoundError:
            # Skip dists whose metadata cannot be read
            continue

        for spec in req_list:
            try:
                req = Requirement(spec)
            except Exception:
                # If parsing fails, ignore this requirement
                continue

            if req.name.lower() == package_name.lower():
                dependents.append(dist_name)
                break

    return dependents


def main():
    package_name = 'torch'
    deps = find_dependents(package_name)

    if deps:
        print(f"Packages depending on {package_name}:")
        for name in sorted(deps):
            print(f"  - {name}")
    else:
        print(f"No packages depend on {package_name}.")


if __name__ == "__main__":
    main()
