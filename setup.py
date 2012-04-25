import os
import sys
from setuptools import setup
import httpie


if sys.argv[-1] == 'test':
    os.system('python tests.py')
    sys.exit()


requirements = ['requests>=0.10.1', 'Pygments>=1.4']
if sys.version_info[:2] in ((2, 6), (3, 1)):
    # argparse has been added in Python 3.2 / 2.7
    requirements.append('argparse>=1.2.1')


setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=open('README.rst').read(),
    url='http://httpie.org/',
    download_url='https://github.com/jkbr/httpie',
    author=httpie.__author__,
    author_email='jakub@roztocil.name',
    license=httpie.__licence__,
    packages=['httpie'],
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
    ],
)
