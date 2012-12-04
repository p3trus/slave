#  -*- coding: utf-8 -*-
#
# Slave, (c) 2012, see AUTHORS.  Licensed under the GNU GPL.

from setuptools import setup

desc = ('A lightweight python package to simplify the communication with '
        'several scientific instruments.')

setup(name='Slave',
      version=__import__('slave').__version__,
      author='Marco Halder',
      author_email='marco.halder@frm2.tum.de',
      license = 'GNU General Public License (GPL), Version 3',
      requires = ['python (>= 2.6)'],
      url='https://github.com/p3trus/slave',
      description=desc,
      long_description=open('README.md').read(),
      packages=['slave']
)
