import os
import sys
from setuptools import setup
import httpie


if sys.argv[-1] == 'test':
    os.system('python tests.py')
    sys.exit()

requirements = ['requests>=0.10.4', 'Pygments>=1.4']

setup(
    name='httpie',
    version=httpie.__version__,
    description=httpie.__doc__.strip(),
    long_description=open('README.rst').read(),
    url='http://httpie.org/',
    download_url='https://github.com/jkbr/httpie',
    author=httpie.__author__,
    author_email=['jakub@roztocil.name', 'kuba.misiorny@gmail.com'],
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1'
        'Programming Language :: Python :: 3.2'
        'Programming Language :: Python :: 3.3'
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
