peepify
=======

Creates a peep-compatible requirements file for a directory of git submodules.

Point peepify at at a directory of git submodules and it'll generate a
requirements file for them!

Requirements: peep must be on your path. If you don't have it, you can get it
from pypi using: pip install peep.

Usage: python peepify.py [-h] --target-dir TARGET_DIR [--tarballs-dir TARBALLS_DIR]
