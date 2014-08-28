#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012-2014, see AUTHORS.  Licensed under the GNU GPL.

import sys

from setuptools import setup, find_packages


desc = ('A lightweight python package to simplify the communication with '
        'several scientific instruments.')

setup(
    name='slave',
    version=__import__('slave').__version__,
    author='Marco Halder',
    author_email='marco.halder@frm2.tum.de',
    license = 'GNU General Public License (GPL), Version 3',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    url='https://github.com/p3trus/slave',
    description=desc,
    long_description=open('README.rst').read(),
    packages=find_packages(),
    include_package_data=True,
)
