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

    $ http --debug <COMPLETE ARGUMENT LIST THAT TRIGGERS THE ERROR>

    <COMPLETE OUTPUT>


2. Contributing Code and Docs
=============================

Before working on a new feature or a bug, please browse `existing issues`_
to see whether it has previously  been discussed.

If your change alters HTTPie’s behaviour or interface, it's a good idea to
discuss it before you start working on it.

If you are fixing an issue, the first step should be to create a test case that
reproduces the incorrect behaviour. That will also help you to build an
understanding of the issue at hand.

**Pull requests introducing code changes without tests
will generally not get merged. The same goes for PRs changing HTTPie’s
behaviour and not providing documentation.**

Conversely, PRs consisting of documentation improvements or tests
for existing-yet-previously-untested behavior will very likely be merged.
Therefore, docs and tests improvements are a great candidate for your first
contribution.

Consider also adding a ``CHANGELOG`` entry for your changes.


Development Environment
--------------------------------


Getting the code
****************

Go to https://github.com/httpie/httpie and fork the project repository.


.. code-block:: bash

    # Clone your fork
    git clone git@github.com:<YOU>/httpie.git

    # Enter the project directory
    cd httpie

    # Create a branch for your changes
    git checkout -b my_topical_branch


Setup
*****

The `Makefile`_ contains a bunch of tasks to get you started. Just run
the following command, which:


* Creates an isolated Python virtual environment inside ``./venv``
  (via the standard library `venv`_ tool);
* installs all dependencies and also installs HTTPie
  (in editable mode so that the ``http`` command will point to your
  working copy).
* and runs tests (It is the same as running ``make install test``).


.. code-block:: bash

    make



Python virtual environment
**************************

Activate the Python virtual environment—created via the ``make install``
task during `setup`_—for your active shell session using the following command:

.. code-block:: bash

    source venv/bin/activate

(If you use ``virtualenvwrapper``, you can also use ``workon httpie`` to
activate the environment — we have created a symlink for you. It’s a bit of
a hack but it works™.)

You should now see ``(httpie)`` next to your shell prompt, and
the ``http`` command should point to your development copy:

.. code-block::

    (httpie) ~/Code/httpie $ which http
    /Users/jakub/Code/httpie/venv/bin/http
    (httpie) ~/Code/httpie $ http --version
    2.0.0-dev

(Btw, you don’t need to activate the virtual environment if you just want
run some of the ``make`` tasks. You can also invoke the development
version of HTTPie directly with ``./venv/bin/http`` without having to activate
the environment first. The same goes for ``./venv/bin/py.test``, etc.).


Making Changes
--------------

Please make sure your changes conform to `Style Guide for Python Code`_ (PEP8)
and that ``make pycodestyle`` passes.


Testing & CI
------------

Please add tests for any new features and bug fixes.

When you open a pull request,
`GitHub Actions <https://github.com/httpie/httpie/actions>`_
will automatically run HTTPie’s `test suite`_ against your code
so please make sure all checks pass.


Running tests locally
*********************

HTTPie uses the `pytest`_ runner.


.. code-block:: bash

    # Run tests on the current Python interpreter with coverage.
    make test

    # Run tests with coverage
    make test-cover

    # Test PEP8 compliance
    make pycodestyle

    # Run extended tests — for code as well as .rst files syntax, packaging, etc.
    make test-all


Running specific tests
**********************

After you have activated your virtual environment (see `setup`_), you
can run specific tests from the terminal:

.. code-block:: bash

    # Run specific tests on the current Python
    py.test tests/test_uploads.py
    py.test tests/test_uploads.py::TestMultipartFormDataFileUpload
    py.test tests/test_uploads.py::TestMultipartFormDataFileUpload::test_upload_ok

-----

See `Makefile`_ for additional development utilities.

Windows
*******

If you are on a Windows machine and not able to run ``make``,
follow the next steps for a basic setup. As a prerequisite, you need to have
Python 3.6+ installed.

Create a virtual environment and activate it:

.. code-block:: powershell

    python -m venv --prompt httpie venv
    venv\Scripts\activate

Install HTTPie in editable mode with all the dependencies:

.. code-block:: powershell

    pip install --upgrade -e . -r requirements-dev.txt

You should now see ``(httpie)`` next to your shell prompt, and
the ``http`` command should point to your development copy:

.. code-block:: powershell

    # In PowerShell:
    (httpie) PS C:\Users\ovezovs\httpie> Get-Command http
    CommandType     Name                                               Version    Source
    -----------     ----                                               -------    ------
    Application     http.exe                                           0.0.0.0    C:\Users\ovezovs\httpie\venv\Scripts\http.exe

.. code-block:: bash

    # In CMD:
    (httpie) C:\Users\ovezovs\httpie> where http
    C:\Users\ovezovs\httpie\venv\Scripts\http.exe
    C:\Users\ovezovs\AppData\Local\Programs\Python\Python38-32\Scripts\http.exe

    (httpie) C:\Users\ovezovs\httpie> http --version
    2.3.0-dev

Use ``pytest`` to run tests locally with an active virtual environment:

.. code-block:: bash

    # Run all tests
    py.test


-----


Finally, feel free to add yourself to `AUTHORS`_!


.. _existing issues: https://github.com/httpie/httpie/issues?state=open
.. _AUTHORS: https://github.com/httpie/httpie/blob/master/AUTHORS.rst
.. _Makefile: https://github.com/httpie/httpie/blob/master/Makefile
.. _venv: https://docs.python.org/3/library/venv.html
.. _pytest: https://pytest.org/
.. _Style Guide for Python Code: https://python.org/dev/peps/pep-0008/
.. _test suite: https://github.com/httpie/httpie/tree/master/tests
