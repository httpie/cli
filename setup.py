from setuptools import setup
from httpie import httpie


setup(name='httpie',version=httpie.__version__,
    description=httpie.__doc__.strip(),
    url='https://github.com/jkbr/httpie',
    author=httpie.__author__,
    license=httpie.__licence__,
    packages=['httpie'],
    entry_points={'console_scripts': ['http = httpie.httpie:main']},
    install_requires=['requests>=0.10.4', 'Pygments>=1.4'])
