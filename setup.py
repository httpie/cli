import os
import sys
import codecs
from setuptools import setup
import httpie


if sys.argv[-1] == 'test':
    status = os.system('python tests/tests.py')
    sys.exit(1 if status > 127 else status)


requirements = [
    'requests>=2.0.0',
    'Pygments>=1.5'
]
try:
    #noinspection PyUnresolvedReferences
    import argparse
except ImportError:
    requirements.append('argparse>=1.2.1')

if 'win32' in str(sys.platform).lower():
    # Terminal colors for Windows
    requirements.append('colorama>=0.2.4')


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=long_description(),
    url='http://httpie.org/',
    download_url='https://github.com/jkbr/httpie',
    author=httpie.__author__,
    author_email='jakub@roztocil.name',
    license=httpie.__licence__,
    packages=['httpie', 'httpie.plugins'],
    entry_points={
        'console_scripts': [
            'http = httpie.__main__:main',
        ],
    },
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
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
