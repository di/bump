import pytest
from click.testing import CliRunner

from bump import SemVer, find_version, main


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

def test_bump_major_with_clear():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(major=True, clear=True)
    check_version(version, 2, 0, 0, None, None)

def test_bump_minor():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(minor=True)
    check_version(version, 1, 3, 3, None, None)

def test_bump_minor_with_clear():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(minor=True, clear=True)
    check_version(version, 1, 3, 0, None, None)

def test_bump_patch():
    version = SemVer(major=1, minor=2, patch=3)
    version.bump(patch=True)
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
    result = runner.invoke(main)
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
