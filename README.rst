bump
====

Bumps package versions.

Example
=======

By default, running ``bump`` in a directory with a ``setup.py`` will bump the
"patch" number in place::

  $ bump
  1.0.1
  $ git diff setup.py
  ─────────────────────────────────────────────────
  modified: setup.py
  ─────────────────────────────────────────────────
  @ setup.py:6 @ from setuptools import setup

  setup(
      name='bump',
  -    version='1.0.0',
  +    version='1.0.1',
      description='Bumps package version numbers',
      long_description=open('README.rst').read(),
      license='MIT',

Conveniently ``bump`` will also return the new version number, so you can use
it after running the command, for example::

  $ export VERSION=`bump`
  $ echo "The new version is $VERSION"
  The new version is 1.0.1

Options
=======

The ``bump`` command can also bump the major or minor version numbers, or set
the pre-release identifier or local version segment::

  $ bump --help
  Usage: bump [OPTIONS] [INPUT] [OUTPUT]

  Options:
    -M, --major     Bump major number. Ex.: 1.2.3 -> 2.2.3
    -m, --minor     Bump minor number. Ex.: 1.2.3 -> 1.3.3
    -p, --patch     Bump patch number. Ex.: 1.2.3 -> 1.2.4
    -r, --reset     Reset subversions. Ex.: Major bump from 1.2.3 will be 2.0.0
                    instead of 2.2.3
    --pre TEXT      Set the pre-release identifier
    --local TEXT    Set the local version segment
    --canonicalize  Canonicalize the new version
    --help          Show this message and exit.

The `--reset` option should be used alongside with minor or major bump.

You can configure these options by setting them in a ``.bump`` or ``setup.cfg``
configuration file as well, so you don't have to specify them every time::

  $ cat .bump
  [bump]
  input = some_directory/__file__.py
  minor = true
  patch = false
  reset = true
