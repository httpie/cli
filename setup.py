# This is purely the result of trial and error.

import sys
import codecs

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import httpie


class PyTest(TestCommand):
    # `$ python setup.py test' simply installs minimal requirements
    # and runs the tests with no fancy stuff like parallel execution.
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_suite = True
        self.test_args = [
            '--doctest-modules', '--verbose',
            './httpie', './tests'
        ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


tests_require = [
    # Pytest needs to come last.
    # https://bitbucket.org/pypa/setuptools/issue/196/
    'pytest-httpbin',
    'pytest',
]


install_requires = [
    'requests>=2.3.0',
    'Pygments>=1.5'
]

### Conditional dependencies:

# sdist
if not 'bdist_wheel' in sys.argv:
    try:
        #noinspection PyUnresolvedReferences
        import argparse
    except ImportError:
        install_requires.append('argparse>=1.2.1')

    if 'win32' in str(sys.platform).lower():
        # Terminal colors for Windows
        install_requires.append('colorama>=0.2.4')


# bdist_wheel
extras_require = {
    # http://wheel.readthedocs.org/en/latest/#defining-conditional-dependencies
    ':python_version == "2.6"'
    ' or python_version == "3.0"'
    ' or python_version == "3.1" ': ['argparse>=1.2.1'],
    ':sys_platform == "win32"': ['colorama>=0.2.4'],
}


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=long_description(),
    url='http://httpie.org/',
    download_url='https://github.com/jakubroztocil/httpie',
    author=httpie.__author__,
    author_email='jakub@roztocil.name',
    license=httpie.__licence__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'http = httpie.__main__:main',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development',
        'Topic :: System :: Networking',
        'Topic :: Terminals',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ],
)
