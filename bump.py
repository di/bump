import configparser
import os
import re
import sys

import click
import toml
from first import first
from packaging.utils import canonicalize_version

pattern = re.compile(r"((?:__)?version(?:__)? ?= ?[\"'])(.+?)([\"'])")


class Config:
    def __init__(self):
        self.ini_config = configparser.RawConfigParser()
        self.ini_config.read([".bump", "setup.cfg"])

        self.toml_config = {}
        if os.path.exists("pyproject.toml"):
            self.toml_config = (
                toml.load("pyproject.toml").get("tool", {}).get("bump", {})
            )

    def get(self, key, coercer=str, default=None):
        candidate = self.toml_config.get(key)
        if candidate is not None:
            # No coercion needed for TOML, since values are strongly typed.
            return candidate

        if coercer is str:
            return self.ini_config.get("bump", key, fallback=default)
        elif coercer is bool:
            return self.ini_config.getboolean("bump", key, fallback=default)
        else:
            raise ValueError(f"invalid coercer: {coercer}")


class SemVer(object):
    def __init__(self, major=0, minor=0, patch=0, pre=None, local=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = pre
        self.local = local

    def __repr__(self):
        # TODO: this is broken
        return "<SemVer {}>".format(
            ", ".join(["{}={}".format(n, getattr(self, n)) for n in self.__slots__])
        )

    def __str__(self):
        version_string = ".".join(map(str, [self.major, self.minor, self.patch]))
        if self.pre:
            version_string += "-" + self.pre
        if self.local:
            version_string += "+" + self.local
        return version_string

    @classmethod
    def parse(cls, version):
        major = minor = patch = 0
        local = pre = None
        local_split = version.split("+")
        if len(local_split) > 1:
            version, local = local_split
        pre_split = version.split("-", 1)
        if len(pre_split) > 1:
            version, pre = pre_split
        major_split = version.split(".", 1)
        if len(major_split) > 1:
            major, version = major_split
            minor_split = version.split(".", 1)
            if len(minor_split) > 1:
                minor, version = minor_split
                if version:
                    patch = version
            else:
                minor = version
        else:
            major = version
        return cls(
            major=int(major), minor=int(minor), patch=int(patch), pre=pre, local=local
        )

    def bump(
        self, major=False, minor=False, patch=False, pre=None, local=None, reset=False
    ):
        if major:
            self.major += 1
            if reset:
                self.minor = 0
                self.patch = 0
        if minor:
            self.minor += 1
            if reset:
                self.patch = 0
        if patch:
            self.patch += 1
        if pre:
            self.pre = pre
        if local:
            self.local = local
        if not (major or minor or patch or pre or local):
            self.patch += 1


class NoVersionFound(Exception):
    pass


def find_version(input_string):
    match = first(pattern.findall(input_string))
    if match is None:
        raise NoVersionFound
    return match[1]


def find_version_in_toml(filepath="pyproject.toml"):
    """Find version in pyproject.toml [project].version field."""
    if not os.path.exists(filepath):
        raise NoVersionFound
    try:
        toml_data = toml.load(filepath)
        version = toml_data.get("project", {}).get("version")
        if version is None:
            raise NoVersionFound
        return version
    except Exception:
        raise NoVersionFound


def update_version_in_toml(new_version, filepath="pyproject.toml"):
    """Update version in pyproject.toml [project].version field."""
    if not os.path.exists(filepath):
        return False
    try:
        # Read file as text to preserve formatting
        with open(filepath, "r", encoding="utf-8") as f:
            contents = f.read()

        # Pattern to match version line in [project] section
        # Matches: version = "1.2.3" or version="1.2.3" or version = '1.2.3', etc.
        # with optional whitespace
        version_pattern = re.compile(
            r'^(\s*version\s*=\s*["\'])(.+?)(["\']\s*)$', re.MULTILINE
        )

        # Find the version line
        match = version_pattern.search(contents)
        if not match:
            return False

        # Replace only the version value, preserving quotes and formatting
        new_contents = version_pattern.sub(
            r"\g<1>{}\g<3>".format(new_version), contents, count=1
        )

        # Write back the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_contents)

        return True
    except Exception:
        return False


@click.command()
@click.option(
    "--major",
    "-M",
    "major",
    flag_value=True,
    default=None,
    help="Bump major number. Ex.: 1.2.3 -> 2.2.3",
)
@click.option(
    "--minor",
    "-m",
    "minor",
    flag_value=True,
    default=None,
    help="Bump minor number. Ex.: 1.2.3 -> 1.3.3",
)
@click.option(
    "--patch",
    "-p",
    "patch",
    flag_value=True,
    default=None,
    help="Bump patch number. Ex.: 1.2.3 -> 1.2.4",
)
@click.option(
    "--reset",
    "-r",
    "reset",
    flag_value=True,
    default=None,
    help="Reset subversions. Ex.: Major bump from 1.2.3 will be 2.0.0 instead of 2.2.3",
)
@click.option("--pre", help="Set the pre-release identifier")
@click.option("--local", help="Set the local version segment")
@click.option(
    "--canonicalize", flag_value=True, default=None, help="Canonicalize the new version"
)
@click.argument("input", type=click.File("rb"), default=None, required=False)
@click.argument("output", type=click.File("wb"), default=None, required=False)
def main(input, output, major, minor, patch, reset, pre, local, canonicalize):
    config = Config()

    major = major or config.get("major", coercer=bool, default=False)
    minor = minor or config.get("minor", coercer=bool, default=False)
    patch = patch or config.get("patch", coercer=bool, default=False)
    reset = reset or config.get("reset", coercer=bool, default=False)
    canonicalize = canonicalize or config.get(
        "canonicalize", coercer=bool, default=False
    )

    # Determine which file to use
    using_toml_only = False
    if input is None:
        # No explicit input provided, detect automatically
        config_input = config.get("input", default=None)
        if config_input:
            # Config specifies an input file
            try:
                input = click.File("rb")(config_input)
            except Exception:
                click.echo("Could not open file: {}".format(config_input))
                sys.exit(1)
        else:
            # Auto-detect: prefer setup.py, fall back to pyproject.toml
            if os.path.exists("setup.py"):
                try:
                    input = click.File("rb")("setup.py")
                except Exception:
                    click.echo("Could not open setup.py")
                    sys.exit(1)
            else:
                # No setup.py, try pyproject.toml
                try:
                    find_version_in_toml("pyproject.toml")
                    using_toml_only = True
                except NoVersionFound:
                    click.echo(
                        "No version found. Neither setup.py nor pyproject.toml with [project].version found."
                    )
                    sys.exit(1)

    # Handle pyproject.toml as primary file
    if using_toml_only:
        try:
            version_string = find_version_in_toml("pyproject.toml")
        except NoVersionFound:
            click.echo("No version found in pyproject.toml [project].version field.")
            sys.exit(1)

        version = SemVer.parse(version_string)
        version.bump(major, minor, patch, pre, local, reset)
        version_string = str(version)
        if canonicalize:
            version_string = canonicalize_version(version_string)

        if update_version_in_toml(version_string, "pyproject.toml"):
            click.echo(version_string)
        else:
            click.echo("Error: Could not update pyproject.toml", err=True)
            sys.exit(1)
        return

    # Handle setup.py (or other Python file) as primary file
    output = output or click.File("wb")(input.name)
    contents = input.read().decode("utf-8")
    try:
        version_string = find_version(contents)
    except NoVersionFound:
        click.echo("No version found in ./{}.".format(input.name))
        sys.exit(1)

    version = SemVer.parse(version_string)
    version.bump(major, minor, patch, pre, local, reset)
    version_string = str(version)
    if canonicalize:
        version_string = canonicalize_version(version_string)
    new = pattern.sub(r"\g<1>{}\g<3>".format(version_string), contents)
    output.write(new.encode())

    # Also bump pyproject.toml if it exists
    if os.path.exists("pyproject.toml"):
        try:
            find_version_in_toml("pyproject.toml")
            if update_version_in_toml(version_string, "pyproject.toml"):
                click.echo("Updated pyproject.toml", err=True)
            else:
                click.echo("Warning: Could not update pyproject.toml", err=True)
        except NoVersionFound:
            # pyproject.toml exists but has no [project].version, continue normally
            pass

    click.echo(version_string)


if __name__ == "__main__":
    main()
