import os
import ast
import pkg_resources


def extract_dependencies():
    """Extract dependencies from setup.py"""
    setup_dir = os.path.join(os.path.dirname(__file__), '..')
    setup_path = os.path.join(setup_dir, 'setup.py')

    with open(setup_path) as f:
        setup_code = f.read()

    setup_ast = ast.parse(setup_code)
    install_requires = []

    for node in ast.walk(setup_ast):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'setup':
            for keyword in node.keywords:
                if keyword.arg == 'install_requires':
                    install_requires = [elt.s for elt in keyword.value.elts]
                    break
            break

    return install_requires


def get_all_dependencies(package_names):
    """Get all dependencies for a list of packages"""
    all_deps = set()
    to_check = set(package_names)

    while to_check:
        package = to_check.pop()
        if package not in all_deps:
            all_deps.add(package)
            try:
                dist = pkg_resources.get_distribution(package)
                requirements = dist.requires()
                to_check.update(req.key for req in requirements)
            except pkg_resources.DistributionNotFound:
                print(f"Warning: {package} not found")

    return all_deps


def get_installed_packages():
    """Get a list of installed packages"""
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    return installed_packages


def main():
    # Extract dependencies from setup.py
    dependencies = extract_dependencies()
    required_libs = get_all_dependencies([pkg_resources.Requirement.parse(dep).key for dep in dependencies])

    # Get installed packages
    installed_libs = get_installed_packages()

    # Identify unused libraries
    unused_libs = installed_libs - required_libs

    # Output unused libraries
    if unused_libs:
        print("Unused libraries:")
        for lib in sorted(unused_libs):
            print(lib)
    else:
        print("No unused libraries found.")


if __name__ == "__main__":
    main()
