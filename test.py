import unittest

from bump import SemVer

from click.testing import CliRunner


class TestBump(unittest.TestCase):

    def check_version(self, version, major, minor, patch, pre, build):
        assert version.major == major
        assert version.minor == minor
        assert version.patch == patch
        assert version.pre == pre
        assert version.build == build

    def test_parse(self):
        version = SemVer.parse("1")
        self.check_version(version, 1, 0, 0, None, None)

        version = SemVer.parse("1.2")
        self.check_version(version, 1, 2, 0, None, None)

        version = SemVer.parse("1.2.3")
        self.check_version(version, 1, 2, 3, None, None)

        version = SemVer.parse("1.2.3-pre")
        self.check_version(version, 1, 2, 3, "pre", None)

        version = SemVer.parse("1.2.3+build")
        self.check_version(version, 1, 2, 3, None, "build")

        version = SemVer.parse("1.2.3-pre+build")
        self.check_version(version, 1, 2, 3, "pre", "build")

    def test_bump(self):
        version = SemVer(major=1, minor=2, patch=3)
        version.bump(major=True)
        self.check_version(version, 2, 2, 3, None, None)

        version = SemVer(major=1, minor=2, patch=3)
        version.bump(minor=True)
        self.check_version(version, 1, 3, 3, None, None)

        version = SemVer(major=1, minor=2, patch=3)
        version.bump(patch=True)
        self.check_version(version, 1, 2, 4, None, None)

        version = SemVer(major=1, minor=2, patch=3)
        version.bump(pre="pre")
        self.check_version(version, 1, 2, 3, "pre", None)

        version = SemVer(major=1, minor=2, patch=3)
        version.bump(build="build")
        self.check_version(version, 1, 2, 3, None, "build")

    def test_cli(self):
        runner = CliRunner()  # noqa


if __name__ == '__main__':
    unittest.main()
