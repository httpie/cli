# This is purely the result of trial and error.

import sys
import codecs

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

import httpie


class PyTest(TestCommand):
    """
    Running `$ python setup.py test' simply installs minimal requirements
    and runs the tests with no fancy stuff like parallel execution.

    """
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--doctest-modules', '--verbose',
            './httpie', './tests'
        ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


tests_require = [
    'pytest-httpbin',
    'pytest',
    'pyopenssl',
    'mock',
]


install_requires = [
    'requests[socks]>=2.22.0',
    'Pygments>=2.5.2',
]
install_requires_win_only = [
    'colorama>=0.2.4',
]

# Conditional dependencies:

# sdist
if 'bdist_wheel' not in sys.argv:

    if 'win32' in str(sys.platform).lower():
        # Terminal colors for Windows
        install_requires.extend(install_requires_win_only)


# bdist_wheel
extras_require = {
    # https://wheel.readthedocs.io/en/latest/#defining-conditional-dependencies
    ':sys_platform == "win32"': install_requires_win_only,
}


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=long_description(),
    url='https://httpie.org/',
    download_url=f'https://github.com/jakubroztocil/httpie/archive/{httpie.__version__}.tar.gz',
    author=httpie.__author__,
    author_email='jakub@roztocil.co',
    license=httpie.__licence__,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'http = httpie.__main__:main',
            'https = httpie.__main__:main',
        ],
    },
    python_requires='>=3.6',
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
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
    project_urls={
        'Documentation': 'https://httpie.org/docs',
        'Source': 'https://github.com/jakubroztocil/httpie',
        'Online Demo': 'https://httpie.org/run',
        'Donate': 'https://httpie.org/donate',
        'Twitter': 'https://twitter.com/clihttp',
    },
)
