######################
Contributing to HTTPie
######################

Bug reports and code and documentation patches are welcome. You can
help this project also by using the development version of HTTPie
and by reporting any bugs you might encounter.

1. Reporting bugs
=================

**It's important that you provide the full command argument list
as well as the output of the failing command.**
Use the ``--debug`` flag and copy&paste both the command and its output
to your bug report, e.g.:

.. code-block:: bash

    $ http --debug [COMPLETE ARGUMENT LIST THAT TRIGGERS THE ERROR]
    [COMPLETE OUTPUT]


2. Contributing Code and Docs
=============================

Before working on a new feature or a bug, please browse `existing issues`_
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to discuss before your starting working on
it.


Creating Development Environment
--------------------------------

Go to https://github.com/jakubroztocil/httpie and fork the project repository.


.. code-block:: bash

    git clone https://github.com/<YOU>/httpie

    cd httpie

    git checkout -b my_topical_branch

    # (Recommended: create a new virtualenv)

    # Install dev. requirements and also HTTPie (in editable mode
    # so that the `http' command will point to your working copy):
    make init


Making Changes
--------------

Please make sure your changes conform to `Style Guide for Python Code`_ (PEP8)
and that ``make pycodestyle`` passes.


Testing
-------

Before opening a pull requests, please make sure the `test suite`_ passes
in all of the `supported Python environments`_. You should also add tests
for any new features and bug fixes.

HTTPie uses `pytest`_ and `Tox`_ for testing.


Running all tests:
******************

.. code-block:: bash

    # Run all tests on the current Python interpreter with coverage
    make test

    # Run all tests in all of the supported and available Pythons via Tox
    make test-tox

    # Run all tests for code as well as packaging, etc.
    make test-all

    # Test PEP8 compliance
    make pycodestyle


Running specific tests:
***********************

.. code-block:: bash

    # Run specific tests on the current Python
    py.test tests/test_uploads.py
    py.test tests/test_uploads.py::TestMultipartFormDataFileUpload
    py.test tests/test_uploads.py::TestMultipartFormDataFileUpload::test_upload_ok

    # Run specific tests on the on all Pythons via Tox
    # (change to `tox -e py37' to limit Python version)
    tox -- tests/test_uploads.py --verbose
    tox -- tests/test_uploads.py::TestMultipartFormDataFileUpload --verbose
    tox -- tests/test_uploads.py::TestMultipartFormDataFileUpload::test_upload_ok --verbose

-----

See `Makefile`_ for additional development utilities.
Don't forget to add yourself to `AUTHORS`_!


.. _Tox: http://tox.testrun.org
.. _supported Python environments: https://github.com/jakubroztocil/httpie/blob/master/tox.ini
.. _existing issues: https://github.com/jakubroztocil/httpie/issues?state=open
.. _AUTHORS: https://github.com/jakubroztocil/httpie/blob/master/AUTHORS.rst
.. _Makefile: https://github.com/jakubroztocil/httpie/blob/master/Makefile
.. _pytest: http://pytest.org/
.. _Style Guide for Python Code: http://python.org/dev/peps/pep-0008/
.. _test suite: https://github.com/jakubroztocil/httpie/tree/master/tests
