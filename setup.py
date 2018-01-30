#! /usr/bin/env python

#sudo python setup.py bdist_wheel
#twine upload ./dist/remdups*.whl

from setuptools import setup
import platform
import os, os.path

__version__ = '1.3'

with open('requirements.txt') as f: requires=f.read().splitlines()
with open('requirements.test.txt') as f: develop=f.read().splitlines()

extras = {
    'develop': develop
}

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name = 'remdups',
    version = __version__,
    description = 'remdups - remove duplicate files',
    license = 'MIT',
    author = 'Roland Puntaier',
    keywords=['Duplicate, File'],
    author_email = 'roland.puntaier@gmail.com',
    url = 'https://github.com/rpuntaie/remdups',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Topic :: Utilities',
        'Topic :: System :: Archiving',
        'Topic :: System :: Systems Administration'
        ],

    install_requires = requires,
    extras_require = {'develop': develop},
    long_description = read('README.rst'),
    packages=['remdups'],
    include_package_data=False,
    zip_safe=False,
    tests_require=[],
    entry_points={
         'console_scripts': [
         'remdups = remdups.remdups:run',
              ]
      },

    )

