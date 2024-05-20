import pkg_resources


def find_dependents(package_name):
    dependents = []
    for dist in pkg_resources.working_set:
        for req in dist.requires():
            if req.project_name.lower() == package_name.lower():
                dependents.append(dist.project_name)
    return dependents


def main():

    package_name = 'torch'

    dependents = find_dependents(package_name)

    if dependents:
        print(f"Packages depending on {package_name}:")
        for dep in dependents:
            print(dep)
    else:
        print(f"No packages depend on {package_name}.")


if __name__ == "__main__":
    main()
