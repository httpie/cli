Contributing to HTTPie
######################

Bug reports and code and documentation patches are greatly appretiated. You can
also help by using the development version of HTTPie and reporting any bugs you
might encounter.

Bug Reports
===========

Along with a description of the problem, please provide the output of the
failing command with the ``--debug`` flag, e.g.:

.. code-block:: bash

    $ http --debug [minimal set of arguments that trigger the error]


Contributing Code and Documentation
===================================

Before working on a new feature or a bug, please browse `existing issues`_
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to discuss before your starting working on
it.


Development Environment
-----------------------

.. code-block:: bash

    git clone https://github.com/<YOU>/httpie

    cd httpie

    git checkout -b my_topical_branch

    # (Recommended: create a new virtualenv)

    # Install dev. requirements:
    pip install -r requirements-dev.txt

    # Install HTTPie in editable mode
    # (the `http' command will point to your working copy):
    pip install --upgrade --force-reinstall --editable .


Making Changes
--------------

Please make sure your changes conform to `Style Guide for Python Code`_ (PEP8).


Tests
-----

Before opening a pull requests, please make sure the `test suite`_ passes
in all of the `supported Python environments`_. You should also **add tests
for any new features and bug fixes**.

HTTPie uses `pytest`_ and `Tox`_.

.. code-block:: bash

    # Run all tests on the current Python:
    python setup.py test

    # Run all tests on all installed supported Pythons:
    tox

    # Run specific tests:
    pytest tests/test_uploads.py


Don't forget to add yourself to `AUTHORS.rst`_.


.. _Tox: http://tox.testrun.org
.. _supported Python environments: https://github.com/jkbr/httpie/blob/master/tox.ini
.. _existing issues: https://github.com/jkbr/httpie/issues?state=open
.. _AUTHORS.rst: https://github.com/jkbr/httpie/blob/master/AUTHORS.rst
.. _pytest: http://pytest.org/
.. _Style Guide for Python Code: http://python.org/dev/peps/pep-0008/
.. _test suite: https://github.com/jkbr/httpie/tree/master/tests
