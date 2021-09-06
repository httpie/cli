# This is purely the result of trial and error.

import sys

from setuptools import setup, find_packages

import httpie

# Note: keep requirements here to ease distributions packaging
tests_require = [
    'pytest',
    'pytest-httpbin>=0.0.6',
    'responses',
]
dev_require = [
    *tests_require,
    'flake8',
    'flake8-comprehensions',
    'flake8-deprecated',
    'flake8-mutable',
    'flake8-tuple',
    'mdformat',
    'pytest-cov',
    'twine',
    'wheel',
]
install_requires = [
    'defusedxml>=0.6.0',
    'requests[socks]>=2.22.0',
    'Pygments>=2.5.2',
    'requests-toolbelt>=0.9.1',
    'setuptools',
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
    'dev': dev_require,
    'test': tests_require,
    # https://wheel.readthedocs.io/en/latest/#defining-conditional-dependencies
    ':sys_platform == "win32"': install_requires_win_only,
}


def long_description():
    with open('README.md', encoding='utf-8') as f:
        return f.read()


setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=long_description(),
    long_description_content_type='text/markdown',
    url='https://httpie.org/',
    download_url=f'https://github.com/httpie/httpie/archive/{httpie.__version__}.tar.gz',
    author=httpie.__author__,
    author_email='jakub@roztocil.co',
    license=httpie.__licence__,
    packages=find_packages(include=['httpie', 'httpie.*']),
    entry_points={
        'console_scripts': [
            'http = httpie.__main__:main',
            'https = httpie.__main__:main',
        ],
    },
    python_requires='>=3.6',
    extras_require=extras_require,
    install_requires=install_requires,
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
        'GitHub': 'https://github.com/httpie/httpie',
        'Twitter': 'https://twitter.com/httpie',
        'Documentation': 'https://httpie.org/docs',
        'Online Demo': 'https://httpie.org/run',
    },
)
