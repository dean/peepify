peepify
=======

Creates a peep-compatible requirements file for a directory of git submodules.

Point peepify at at a directory of git submodules and it'll generate a
requirements file for them!

Usage::

    python peepify.py [-h] --target-dir TARGET_DIR [--tarballs-dir TARBALLS_DIR]


Example::

    $ cd fjord
    $ peepify.py --target-dir vendor/src/ --tarballs_dir tarballs/


Requirements:

* requests
* peep

``peep`` must be on your path. If you don't have it on your path, consult
the peep documentation to install it: https://github.com/erikrose/peep
