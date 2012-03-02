import sys
from setuptools import setup
import httpie


requirements = ['requests>=0.10.4', 'Pygments>=1.4']

if sys.version_info < (2 , 7):
    requirements.append('argparse>=1.2.1')


setup(name='httpie',version=httpie.__version__,
    description=httpie.__doc__.strip(),
    url='https://github.com/jkbr/httpie',
    author=httpie.__author__,
    license=httpie.__licence__,
    packages=['httpie'],
    entry_points={'console_scripts': ['http = httpie.__main__:main']},
    install_requires=requirements)
