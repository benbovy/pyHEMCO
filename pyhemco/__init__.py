# -*- coding: utf-8 -*-
"""
PyHEMCO
=======

A Python API for the Harvard Emissions Component (HEMCO).

:copyright: Copyright 2013-2014 by Benoît Bovy and Christoff Keller.
:license: GPLv3, see LICENSE.txt for details.

"""

__version__ = '0.1.0dev'
__license__ = __doc__
__project_url__ = 'https://github.com/benbovy/PyHEMCO'

# Check python version
import sys
if sys.version_info[:2] < (2, 7):
    raise ImportError("Python version 2.7.x is required for PyHEMCO"
                      " ({}.{} detected).".format(*sys.version_info[:2]))
if sys.version_info.major > 2:
    raise ImportError("PyHEMCO is not yet compatible with Python 3.x")
