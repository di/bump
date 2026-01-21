from pathlib import Path

import pytest
import toml
from click.testing import CliRunner

from bump import (
    Config,
    NoVersionFound,
    SemVer,
    find_version,
    find_version_in_toml,
    main,
    update_version_in_toml,
)


def check_version(version, major, minor, patch, pre, local):
    assert version.major == major
    assert version.minor == minor
    assert version.patch == patch
    assert version.pre == pre
    assert version.local == local


@pytest.mark.parametrize(
    "version,args",
    [
        ("1", (1, 0, 0, None, None)),
        ("1.2", (1, 2, 0, None, None)),
        ("1.2.3", (1, 2, 3, None, None)),
        ("1.2.3-pre", (1, 2, 3, "pre", None)),
        ("1.2.3+local", (1, 2, 3, None, "local")),
        ("1.2.3-pre+local", (1, 2, 3, "pre", "local")),
    ],
)
def test_parse(version, args):
    check_version(SemVer.parse(version), *args)


@pytest.mark.parametrize(
    "version,expected",
    [
        ("1", "1.0.0"),
        ("1.2", "1.2.0"),
        ("1.2.3", "1.2.3"),
        ("1.2.3-pre", "1.2.3-pre"),
        ("1.2.3+local", "1.2.3+local"),
        ("1.2.3-pre+local", "1.2.3-pre+local"),
    ],
)
def test_str(version, expected):
    assert str(SemVer.parse(version)) == expected


def test_bump_major():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(major=True)
    check_version(version, 2, 2, 3, None, None)


def test_bump_major_with_reset():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(major=True, reset=True)
    check_version(version, 2, 0, 0, None, None)


def test_bump_minor():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(minor=True)
    check_version(version, 1, 3, 3, None, None)


def test_bump_minor_with_reset():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(minor=True, reset=True)
    check_version(version, 1, 3, 0, None, None)


def test_bump_patch():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(patch=True)
    check_version(version, 1, 2, 4, None, None)


def test_bump_patch_with_reset():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(patch=True, reset=True)
    check_version(version, 1, 2, 4, None, None)


def test_bump_pre():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(pre="pre")
    check_version(version, 1, 2, 3, "pre", None)


def test_bump_local():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(local="local")
    check_version(version, 1, 2, 3, None, "local")


def test_bump_no_args_retains_pre():
    version = SemVer(major=1, pre="pre")
    version.bump()
    check_version(version, 1, 0, 1, "pre", None)


def test_bump_no_args_retains_local():
    version = SemVer(major=1, local="local")
    version.bump()
    check_version(version, 1, 0, 1, None, "local")


def test_cli():
    runner = CliRunner()
    result = runner.invoke(main, args="pyproject.toml")
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "line,expected",
    [
        ('__version__ = "1.2.3"', "1.2.3"),
        ("__version__ = '1.2.3'", "1.2.3"),
        ('__version__="1.2.3"', "1.2.3"),
        ("__version__='1.2.3'", "1.2.3"),
        ("    version='1.2.3',", "1.2.3"),
        ('    version="1.2.3",', "1.2.3"),
        ('    version="1.2.3-dev",', "1.2.3-dev"),
        ('    version="1.2.3+rc4",', "1.2.3+rc4"),
    ],
)
def test_find_version(line, expected):
    assert find_version(line) == expected


def test_config_toml(tmp_path, monkeypatch):
    config = """
    [tool.bump]
    major = true
    minor = true
    patch = true
    reset = true
    input = "foobar.py"
    canonicalize = true
    """

    file = tmp_path / "pyproject.toml"
    file.write_text(config)

    monkeypatch.chdir(tmp_path)
    assert (Path.cwd() / "pyproject.toml").is_file()

    config = Config()
    assert config.get("major", coercer=bool, default=False)
    assert config.get("minor", coercer=bool, default=False)
    assert config.get("patch", coercer=bool, default=False)
    assert config.get("reset", coercer=bool, default=False)
    assert config.get("input", default="setup.py") == "foobar.py"
    assert config.get("canonicalize")

    # defaults also work
    assert config.get("nosuchkey") is None
    assert config.get("nosuchkey", default="default") == "default"


def test_config_ini(tmp_path, monkeypatch):
    config = """
    [bump]
    major = yes
    minor = true
    patch = 1
    reset = yes
    input = foobar.py
    canonicalize = yes
    """

    file = tmp_path / ".bump"
    file.write_text(config)

    monkeypatch.chdir(tmp_path)
    assert (Path.cwd() / ".bump").is_file()

    config = Config()
    assert config.get("major", coercer=bool, default=False)
    assert config.get("minor", coercer=bool, default=False)
    assert config.get("patch", coercer=bool, default=False)
    assert config.get("reset", coercer=bool, default=False)
    assert config.get("input") == "foobar.py"
    assert config.get("canonicalize")

    # defaults also work
    assert config.get("nosuchkey") is None
    assert config.get("nosuchkey", default="default") == "default"
    assert config.get("nosuchbool", coercer=bool, default=True) is True


def test_find_version_in_toml(tmp_path, monkeypatch):
    """Test finding version in pyproject.toml [project].version field."""
    pyproject = """
[project]
name = "test-package"
version = "1.2.3"
    """
    file = tmp_path / "pyproject.toml"
    file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)
    version = find_version_in_toml("pyproject.toml")
    assert version == "1.2.3"


def test_find_version_in_toml_no_file(tmp_path, monkeypatch):
    """Test that NoVersionFound is raised when pyproject.toml doesn't exist."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(NoVersionFound):
        find_version_in_toml("pyproject.toml")


def test_find_version_in_toml_no_project_section(tmp_path, monkeypatch):
    """Test that NoVersionFound is raised when [project] section is missing."""
    pyproject = """
[build-system]
requires = ["setuptools"]
    """
    file = tmp_path / "pyproject.toml"
    file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)
    with pytest.raises(NoVersionFound):
        find_version_in_toml("pyproject.toml")


def test_find_version_in_toml_no_version(tmp_path, monkeypatch):
    """Test that NoVersionFound is raised when version field is missing."""
    pyproject = """
[project]
name = "test-package"
    """
    file = tmp_path / "pyproject.toml"
    file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)
    with pytest.raises(NoVersionFound):
        find_version_in_toml("pyproject.toml")


def test_update_version_in_toml(tmp_path, monkeypatch):
    """Test updating version in pyproject.toml."""
    pyproject = """
[project]
name = "test-package"
version = "1.2.3"
description = "A test package"
    """
    file = tmp_path / "pyproject.toml"
    file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)
    result = update_version_in_toml("2.0.0", "pyproject.toml")
    assert result is True

    # Verify the version was updated
    updated = find_version_in_toml("pyproject.toml")
    assert updated == "2.0.0"

    # Verify other fields are preserved
    data = toml.load(file)
    assert data["project"]["name"] == "test-package"
    assert data["project"]["description"] == "A test package"


def test_update_version_in_toml_no_file(tmp_path, monkeypatch):
    """Test that update returns False when pyproject.toml doesn't exist."""
    monkeypatch.chdir(tmp_path)
    result = update_version_in_toml("2.0.0", "pyproject.toml")
    assert result is False


def test_update_version_in_toml_no_project_section(tmp_path, monkeypatch):
    """Test that update returns False when [project] section is missing."""
    pyproject = """
[build-system]
requires = ["setuptools"]
    """
    file = tmp_path / "pyproject.toml"
    file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)
    result = update_version_in_toml("2.0.0", "pyproject.toml")
    assert result is False


def test_cli_bumps_both_files(tmp_path, monkeypatch):
    """Test that CLI bumps both setup.py and pyproject.toml when both exist."""
    setup_py = """
from setuptools import setup

setup(
    name='test-package',
    version='1.0.0',
    description='Test package',
)
    """
    pyproject = """
[project]
name = "test-package"
version = "1.0.0"
description = "Test package"
    """

    setup_file = tmp_path / "setup.py"
    setup_file.write_text(setup_py)

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=["setup.py"])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify setup.py was updated
    setup_contents = setup_file.read_text()
    assert "version='1.0.1'" in setup_contents

    # Verify pyproject.toml was updated
    pyproject_data = toml.load(pyproject_file)
    assert pyproject_data["project"]["version"] == "1.0.1"


def test_cli_only_setup_py(tmp_path, monkeypatch):
    """Test backward compatibility when only setup.py exists."""
    setup_py = """
from setuptools import setup

setup(
    name='test-package',
    version='1.0.0',
    description='Test package',
)
    """

    setup_file = tmp_path / "setup.py"
    setup_file.write_text(setup_py)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=["setup.py"])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify setup.py was updated
    setup_contents = setup_file.read_text()
    assert "version='1.0.1'" in setup_contents


def test_cli_pyproject_toml_without_version(tmp_path, monkeypatch):
    """Test that script continues when pyproject.toml exists but has no [project].version."""
    setup_py = """
from setuptools import setup

setup(
    name='test-package',
    version='1.0.0',
    description='Test package',
)
    """
    pyproject = """
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
    """

    setup_file = tmp_path / "setup.py"
    setup_file.write_text(setup_py)

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=["setup.py"])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify setup.py was updated
    setup_contents = setup_file.read_text()
    assert "version='1.0.1'" in setup_contents

    # Verify pyproject.toml was NOT modified (no version to update)
    pyproject_data = toml.load(pyproject_file)
    assert "project" not in pyproject_data or "version" not in pyproject_data.get(
        "project", {}
    )


def test_cli_only_pyproject_toml(tmp_path, monkeypatch):
    """Test that script works when only pyproject.toml exists (no setup.py)."""
    pyproject = """
[project]
name = "test-package"
version = "1.0.0"
description = "Test package"

[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
    """

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=[])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify pyproject.toml was updated
    pyproject_data = toml.load(pyproject_file)
    assert pyproject_data["project"]["version"] == "1.0.1"


def test_cli_prioritizes_setup_py(tmp_path, monkeypatch):
    """Test that script prioritizes setup.py when both files exist."""
    setup_py = """
from setuptools import setup

setup(
    name='test-package',
    version='1.0.0',
    description='Test package',
)
    """
    pyproject = """
[project]
name = "test-package"
version = "2.0.0"
description = "Test package"
    """

    setup_file = tmp_path / "setup.py"
    setup_file.write_text(setup_py)

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=[])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify setup.py was updated (takes priority)
    setup_contents = setup_file.read_text()
    assert "version='1.0.1'" in setup_contents

    # Verify pyproject.toml was also updated to match
    pyproject_data = toml.load(pyproject_file)
    assert pyproject_data["project"]["version"] == "1.0.1"


def test_cli_no_version_found(tmp_path, monkeypatch):
    """Test that script fails gracefully when neither file has a version."""
    # Create a directory with neither setup.py nor pyproject.toml with version
    pyproject = """
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
    """

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=[])
    assert result.exit_code != 0
    assert "No version found" in result.output


def test_cli_explicit_input_still_works(tmp_path, monkeypatch):
    """Test that explicit input file argument still works."""
    custom_file = tmp_path / "custom.py"
    custom_file.write_text('__version__ = "1.0.0"')

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=["custom.py"])
    assert result.exit_code == 0
    assert "1.0.1" in result.output

    # Verify custom file was updated
    contents = custom_file.read_text()
    assert '__version__ = "1.0.1"' in contents


def test_cli_pyproject_toml_only_major_bump(tmp_path, monkeypatch):
    """Test major version bump with pyproject.toml-only project."""
    pyproject = """
[project]
name = "test-package"
version = "1.2.3"
description = "Test package"
    """

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject)

    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, args=["--major", "--reset"])
    assert result.exit_code == 0
    assert "2.0.0" in result.output

    # Verify pyproject.toml was updated
    pyproject_data = toml.load(pyproject_file)
    assert pyproject_data["project"]["version"] == "2.0.0"
