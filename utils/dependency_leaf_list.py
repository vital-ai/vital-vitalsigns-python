import pkg_resources


def find_leaf_packages():
    all_packages = {dist.project_name.lower() for dist in pkg_resources.working_set}
    dependencies = set()

    for dist in pkg_resources.working_set:
        for req in dist.requires():
            dependencies.add(req.project_name.lower())

    leaf_packages = all_packages - dependencies
    return leaf_packages


def main():

    leaf_packages = find_leaf_packages()

    if leaf_packages:
        print("Packages that would be removed:")
        for pkg in leaf_packages:
            print(pkg)
    else:
        print("No packages would be removed.")


if __name__ == "__main__":
    main()
