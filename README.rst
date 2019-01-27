Archive Tools
=============

This package provides tools for managing archives.  An archive in
terms of this package is a compressed tar archive file with some
embedded metadata on the included files.  The metadata include the
name, file stats, and checksums of the file.

The package provides (actually, is supposed to provide) command line
tools to enable the following tasks:

+ Create an archive, takes a list of files to include in the archive
  as input.

+ Check the integrity and consistency of an archive.

+ List the contents of the archive.

+ Display details on a file in an archive.

+ Given a list of files as input, list those files that are either not
  in the archive or where the file in the archive differs.

All tasks providing information on an archive should take this
information from the embedded metadata.  Retrieving this metadata
should not require reading through the compressed tar archive.


System requirements
-------------------

Python:

+ Python 3.4 or newer.

Required library packages:

+ `PyYAML`_

Optional library packages:

+ `pytest`_

  Only needed to run the test suite.

+ `distutils-pytest`_

  Only needed to run the test suite.


Installation
------------

This package uses the distutils Python standard library package and
follows its conventions of packaging source distributions.  See the
documentation on `Installing Python Modules`_ for details or to
customize the install process.

1. Download the sources, unpack, and change into the source directory.

2. Build::

     $ python setup.py build

3. Test (not yet implemented)::

     $ python setup.py test

4. Install::

     $ python setup.py install

The last step might require admin privileges in order to write into
the site-packages directory of your Python installation.


Copyright and License
---------------------

Copyright 2019 Rolf Krahl

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.  You may
obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.



.. _PyYAML: http://pyyaml.org/wiki/PyYAML
.. _pytest: http://pytest.org/
.. _distutils-pytest: https://github.com/RKrahl/distutils-pytest
.. _Installing Python Modules: https://docs.python.org/3.7/install/