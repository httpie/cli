# Contributing to HTTPie

Bug reports and code and documentation patches are welcome. You can
help this project also by using the development version of HTTPie
and by reporting any bugs you might encounter.

## 1. Reporting bugs

**It's important that you provide the full command argument list
as well as the output of the failing command.**

Use the `--debug` flag and copy&paste both the command and its output
to your bug report, e.g.:

```bash
$ http --debug <COMPLETE ARGUMENT LIST THAT TRIGGERS THE ERROR>
<COMPLETE OUTPUT>
```

## 2. Contributing Code and Docs

Before working on a new feature or a bug, please browse [existing issues](https://github.com/httpie/cli/issues)
to see whether it has previously been discussed.

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

Consider also adding a [CHANGELOG](https://github.com/httpie/cli/blob/master/CHANGELOG.md) entry for your changes.

### Development Environment

#### Getting the code

Go to <https://github.com/httpie/cli> and fork the project repository.

```bash
# Clone your fork
$ git clone git@github.com:<YOU>/httpie.git

# Enter the project directory
$ cd httpie

# Create a branch for your changes
$ git checkout -b my_topical_branch
```

#### Setup

The [Makefile](https://github.com/httpie/cli/blob/master/Makefile) contains a bunch of tasks to get you started.
You can run `$ make` to see all the available tasks.

To get started, run the command below, which:

- Creates an isolated Python virtual environment inside `./venv`
  (via the standard library [venv](https://docs.python.org/3/library/venv.html) tool);
- installs all dependencies and also installs HTTPie
  (in editable mode so that the `http` command will point to your
  working copy).
- and runs tests (It is the same as running `make install test`).

```bash
$ make all
```

#### Python virtual environment

Activate the Python virtual environment—created via the `make install`
task during [setup](#setup) for your active shell session using the following command:

```bash
$ source venv/bin/activate
```

(If you use `virtualenvwrapper`, you can also use `workon httpie` to
activate the environment — we have created a symlink for you. It’s a bit of
a hack but it works™.)

You should now see `(httpie)` next to your shell prompt, and
the `http` command should point to your development copy:

```bash
(httpie) ~/Code/httpie $ which http
/Users/<user>/Code/httpie/venv/bin/http
(httpie) ~/Code/httpie $ http --version
2.0.0-dev
```

(Btw, you don’t need to activate the virtual environment if you just want
run some of the `make` tasks. You can also invoke the development
version of HTTPie directly with `./venv/bin/http` without having to activate
the environment first. The same goes for `./venv/bin/pytest`, etc.).

### Making Changes

Please make sure your changes conform to [Style Guide for Python Code](https://python.org/dev/peps/pep-0008/) (PEP8)
and that `make pycodestyle` passes.

### Testing & CI

Please add tests for any new features and bug fixes.

When you open a Pull Request, [GitHub Actions](https://github.com/httpie/cli/actions) will automatically run HTTPie’s [test suite](https://github.com/httpie/cli/tree/master/tests) against your code, so please make sure all checks pass.

#### Running tests locally

HTTPie uses the [pytest](https://pytest.org/) runner.

```bash
# Run tests on the current Python interpreter with coverage.
$ make test

# Run tests with coverage
$ make test-cover

# Test PEP8 compliance
$ make codestyle

# Run extended tests — for code as well as .md files syntax, packaging, etc.
$ make test-all
```

#### Running specific tests

After you have activated your virtual environment (see [setup](#setup)), you
can run specific tests from the terminal:

```bash
# Run specific tests on the current Python
$ python -m pytest tests/test_uploads.py
$ python -m pytest tests/test_uploads.py::TestMultipartFormDataFileUpload
$ python -m pytest tests/test_uploads.py::TestMultipartFormDataFileUpload::test_upload_ok
```

See [Makefile](https://github.com/httpie/cli/blob/master/Makefile) for additional development utilities.

#### Running benchmarks

If you are trying to work on speeding up HTTPie and want to verify your results, you
can run the benchmark suite. The suite will compare the last commit of your branch
with the master branch of your repository (or a fresh checkout of HTTPie master, through
`--fresh`) and report the results back.

```bash
$ python extras/profiling/run.py
```

The benchmarks can also be run on the CI. Since it is a long process, it requires manual
oversight. Ping one of the maintainers to get a `benchmark` label on your branch.

#### Windows

If you are on a Windows machine and not able to run `make`,
follow the next steps for a basic setup. As a prerequisite, you need to have
Python 3.7+ installed.

Create a virtual environment and activate it:

```powershell
C:\> python -m venv --prompt httpie venv
C:\> venv\Scripts\activate
```

Install HTTPie in editable mode with all the dependencies:

```powershell
C:\> python -m pip install --upgrade -e .[dev]
```

You should now see `(httpie)` next to your shell prompt, and
the `http` command should point to your development copy:

```powershell
# In PowerShell:
(httpie) PS C:\Users\<user>\httpie> Get-Command http
CommandType     Name                                               Version    Source
-----------     ----                                               -------    ------
Application     http.exe                                           0.0.0.0    C:\Users\<user>\httpie\venv\Scripts\http.exe
```

```bash
# In CMD:
(httpie) C:\Users\<user>\httpie> where http
C:\Users\<user>\httpie\venv\Scripts\http.exe
C:\Users\<user>\AppData\Local\Programs\Python\Python38-32\Scripts\http.exe

(httpie) C:\Users\<user>\httpie> http --version
2.3.0-dev
```

Use `pytest` to run tests locally with an active virtual environment:

```bash
# Run all tests
$ python -m pytest
```

______________________________________________________________________

Finally, feel free to add yourself to [AUTHORS](https://github.com/httpie/cli/blob/master/AUTHORS.md)!
