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
    name='Slave',
    version=__import__('slave').__version__,
    author='Marco Halder',
    author_email='marco.halder@frm2.tum.de',
    license = 'GNU General Public License (GPL), Version 3',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    url='https://github.com/p3trus/slave',
    description=desc,
    long_description=open('README.md').read(),
    packages=['slave', 'slave.test'],
    # make sure to add custom_fixers to the MANIFEST.in 
    include_package_data=True,
    **extra
)
