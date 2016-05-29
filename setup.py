#! /usr/bin/env python

from setuptools import setup
import platform
import os, os.path

__version__ = '1.2'

requires = []

extras = {
    'develop': [
        'Pillow>=2.1.0',
        'pytest>=2.4.1',
        'pytest-cov>=1.6'
    ]
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'Topic :: Utilities',
        'Topic :: System :: Archiving',
        'Topic :: System :: Systems Administration'
        ],

    install_requires = requires,
    extras_require = extras,
    long_description = read('README.rst'),
    packages=['remdups'],
    include_package_data=False,
    zip_safe=False,
    tests_require=[],
    entry_points={
         'console_scripts': [
         'remdups = remdups.remdups:main',
              ]
      },

    )

