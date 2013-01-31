#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

import sys

from setuptools import setup


desc = ('A lightweight python package to simplify the communication with '
        'several scientific instruments.')
# if we are running on python 3, enable 2to3.
extra = {}
if sys.version_info >= (3, 0):
    extra.update(
        use_2to3=True,
    )


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
    packages=['slave', 'slave.test'],
    # make sure to add custom_fixers to the MANIFEST.in 
    include_package_data=True,
    **extra
)
