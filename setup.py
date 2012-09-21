import os
import sys
import re
import codecs
from setuptools import setup
import httpie


if sys.argv[-1] == 'test':
    status = os.system('python tests/tests.py')
    sys.exit(1 if status > 127 else status)


requirements = [
    # Debian has only requests==0.10.1 and httpie.deb depends on that.
    'requests>=0.10.1',
    'Pygments>=1.5'
]
if sys.version_info[:2] in ((2, 6), (3, 1)):
    # argparse has been added in Python 3.2 / 2.7
    requirements.append('argparse>=1.2.1')
if 'win32' in str(sys.platform).lower():
    # Terminal colors for Windows
    requirements.append('colorama>=0.2.4')


def long_description():
    """Pre-process the README so that PyPi can render it properly."""
    with codecs.open('README.rst', encoding='utf8') as f:
        rst = f.read()
    code_block = '(:\n\n)?\.\. code-block::.*'
    rst = re.sub(code_block, '::', rst)
    return rst


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
    packages=['httpie'],
    entry_points={
        'console_scripts': [
            'http = httpie.__main__:main',
            # Not ready yet.
            # 'httpie = httpie.manage:main',
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
