import pytest

import generate_package_list


def _generate_raw_package_input(
    name: str = "package_name",
    version: str = "1.0.0",
    depends: list[str] | None = None,
    imports: list[str] | None = None,
    linking_to: list[str] | None = None,
) -> str:
    """Generate raw package input for testing purposes.

    :param name: Name of the package
    :param version: Version of the package
    :param depends: The Depends of the package
    :param imports: The Imports of the package
    :param linking_to: The LinkingTo of the package
    :return: Raw package input
    """
    package_input_list = [f"Package: {name}", f"Version: {version}"]

    if depends is not None:
        package_input_list.append(f"Depends: {', '.join(depends)}")

    if imports is not None:
        package_input_list.append(f"Imports: {', '.join(imports)}")

    if linking_to is not None:
        package_input_list.append(f"LinkingTo: {', '.join(linking_to)}")

    package_input_list.extend(["License: GPL-3", "NeedsCompilation: no"])

    return "\n".join(package_input_list)


def test_r_package_from_raw_name_and_version() -> None:
    """Test that RPackage instance can be created from raw input."""
    # GIVEN raw package input
    name = "some_other_package_name"
    version = "0.0.1"
    raw_package_input = _generate_raw_package_input(name, version)

    # WHEN a RPackage instance is created from this input
    r_package = generate_package_list.RPackage.from_raw(raw_package_input)

    # THEN the RPackage contains the correct name
    assert r_package.name == name
    # AND the RPackage contains the correct version number
    assert r_package.version == version


@pytest.mark.parametrize("deps_key", ["depends", "imports", "linking_to"])
def test_r_package_from_raw_deps(deps_key: str) -> None:
    """RPackage should include different dependencies in the deps."""
    # GIVEN raw package input with specified deps
    deps = ["package_one", "package_two"]
    raw_package_input = _generate_raw_package_input(**{deps_key: deps})

    # WHEN a RPackage instance is created from this input
    r_package = generate_package_list.RPackage.from_raw(raw_package_input)

    # THEN the RPackage contains the correct deps
    assert all([depend in r_package.deps for depend in deps])
