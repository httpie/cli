from setuptools import setup


setup(name='httpie',version='0.1.1',
    description='cURL for humans',
    url='https://github.com/jkbr/httpie',
    author='Jakub Roztocil',
    license='BSD',
    packages=['httpie'],
    entry_points={'console_scripts': ['httpie = httpie.httpie:main']},
    install_requires=['requests>=0.10.4', 'Pygments>=1.4'])
