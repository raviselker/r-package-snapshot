"""Module to generate a full dependency list from list of packages."""
import argparse
import dataclasses
import pathlib
import re
import subprocess
from urllib import request

import toposort

re_line_fixer = re.compile(r"(\n +)", re.MULTILINE)
re_key_value = re.compile(r"^([A-Za-z0-9]+):\s*(.+)$", re.MULTILINE)
re_pkg_name = re.compile(r"[A-Za-z][A-Za-z0-9_\.]+")


R_INCLUDED = [
    "R",  # base
    "base",
    "compiler",
    "datasets",
    "graphics",
    "grDevices",
    "grid",
    "methods",
    "parallel",
    "splines",
    "stats",
    "stats4",
    "tcltk",
    "utils",
    "tools",
    "KernSmooth",  # recommended
    "MASS",
    "Matrix",
    "boot",
    "class",
    "cluster",
    "codetools",
    "foreign",
    "lattice",
    "mgcv",
    "nlme",
    "nnet",
    "rpart",
    "spatial",
    "survival",
]


@dataclasses.dataclass
class RPackage:
    """An R package class."""

    name: str
    version: str
    deps: set[str]

    @property
    def full_name(self) -> str:
        """Full name of package (including version number)."""
        return f"{self.name}_{self.version}"

    @classmethod
    def from_raw(cls, raw_input: str) -> "RPackage":
        """Create RPackage object from raw string.

        :param raw_input: The raw string to parse
        :return: An RPackage instance
        """
        raw_input = re_line_fixer.sub(" ", raw_input)
        input_dict = dict(re_key_value.findall(raw_input))

        name = input_dict["Package"]
        version = input_dict["Version"]

        deps = []
        if "Depends" in input_dict:
            deps = re_pkg_name.findall(input_dict["Depends"])

        if "Imports" in input_dict:
            imps = re_pkg_name.findall(input_dict["Imports"])
            deps.extend(imps)

        if "LinkingTo" in input_dict:
            link = re_pkg_name.findall(input_dict["LinkingTo"])
            deps.extend(link)

        return cls(name, version, set(deps))

    def download(self, repo_url: str) -> None:
        """Download the R package from specified repo.

        :param repo_url: Url from repo to download package from
        """
        subprocess.run(
            f'wget "{repo_url}/{self.full_name}.tar.gz" -O "{self.full_name}.tar.gz"',
            shell=True,
            check=True,
        )

    def build(self) -> None:
        """Build the R package."""
        subprocess.run(
            f'R CMD INSTALL --build "{self.full_name}.tar.gz"', shell=True, check=True
        )


def main() -> None:
    """Generate a topological dependency list.

    Optionally builds the packages in the list.
    """
    args = _parse_args()
    repo_url = args.url
    main_dependencies_file_path = args.src

    # Generate a list of all packages in the repo
    raw_repo_package_list = _download_raw_repo_package_list(repo_url)
    repo_package_list = _parse_repo_package_list(raw_repo_package_list)

    # Generate a topological list of dependencies (and sub-dependencies)
    # from src file
    dependencies = _generate_full_dependency_list(
        main_dependencies_file_path, repo_package_list
    )
    print(dependencies)

    # Optionally, download and build the dependencies
    if args.build:
        _download_and_build_dependencies(dependencies, repo_url)


def _parse_args() -> argparse.Namespace:
    """Define command-line arguments and parse them.

    :return: The arguments returned from argparse
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate list of packages and optionally build the packages in the list."
        )
    )
    parser.add_argument("src", type=pathlib.Path, help="Path to package list")
    parser.add_argument("url", type=str, help="Url to the repo")
    parser.add_argument(
        "-b", "--build", action="store_true", help="Download and build the packages"
    )
    return parser.parse_args()


def _download_raw_repo_package_list(url: str) -> str:
    """Download the repo package list from specified url.

    :param url: The url to the repo
    :return: A raw list of all packages in the repo
    """
    with request.urlopen(f"{url}/PACKAGES") as response:
        return response.read().decode("utf-8")


def _parse_repo_package_list(raw_repo_package_list: str) -> dict[str, RPackage]:
    """Parse the raw repo package list into list of RPackage instances.

    :param raw_repo_package_list: Raw package list
    :return: List of RPackages that the repo contains
    """
    return {
        r_package.name: r_package
        for r_package in [
            RPackage.from_raw(pkg)
            for pkg in raw_repo_package_list.split("\n\n")
            if pkg.startswith("Package:")
        ]
    }


def _generate_full_dependency_list(
    main_dependencies_file_path: pathlib.Path, repo_package_list: dict[str, RPackage]
) -> list[RPackage]:
    """Generates a list of all (sub) dependencies.

    :param main_dependencies_file_path: Path to file containing main
      dependencies
    :param repo_package_list: List of packages in the repo
    :return: A topological list containing all dependencies and sub-dependencies
    """

    with open(main_dependencies_file_path, "r", encoding="utf-8") as main_dependencies:
        packages = [package_name.strip() for package_name in main_dependencies]
        packages_set = set(packages)
        for package in packages:
            deps = _get_sub_dependencies(package, repo_package_list)
            packages_set.update(deps)

        pkgs_dict = {
            name: repo_package_list[name].deps
            for name in packages_set
            if name not in R_INCLUDED
        }

        packages = toposort.toposort_flatten(pkgs_dict)

        return [
            repo_package_list[package]
            for package in packages
            if package not in R_INCLUDED
        ]


def _get_sub_dependencies(
    name: str, repo_package_list: dict[str, RPackage]
) -> set[str]:
    """Returns the dependencies of a package.

    :param name: Name of the main package
    :param repo_package_list: List of all packages in the repo
    :return: A set of dependencies of the package
    """
    package = repo_package_list[name]
    deps = set(package.deps)
    for dep in package.deps:
        if dep in R_INCLUDED:
            continue
        dep_deps = _get_sub_dependencies(dep, repo_package_list)
        deps.update(dep_deps)
    return deps


def _download_and_build_dependencies(
    package_list: list[RPackage], repo_url: str
) -> None:
    """Downloads and builds a list of R packages.

    :param package_list: List of packages to build
    :param repo_url: Url of the repo to download packages from
    """
    for package in package_list:
        package.download(repo_url)
        package.build()


if __name__ == "__main__":
    main()
