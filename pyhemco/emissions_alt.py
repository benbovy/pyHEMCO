# -*- coding: utf-8 -*-

# part of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2013 Benoit Bovy
# see license.txt for more details
# 
#

"""
A Python API for the Harvard Emissions Component (HEMCO) of GEOS-Chem.

"""

import os

import numpy as np

import timetools
from datatypes import ObjectCollection


BUILTIN_SETTINGS_PATH = 'path/to/default/settings/files'

#-----------------------------------------------------------------------------
# Generic classes or functions (not part of the public HEMCO API)
# will be replaced or moved elsewhere.
#-----------------------------------------------------------------------------

class BaseField(object):
    """
    Base class for GEOS-Chem fields.
    
    Parameters
    ----------
    name : string
        Field descriptive name
    standard_name : string
        Field (variable) standard name.
    ndim : int
        Data dimensions (number)
    unit : string
        Unit of data.
    filename : string
        Filename or path to the file where data is stored.
    timestamp : string
        time stamp of interest. Used to selected data only for particular
        time slices (see :func:`timetools.strptimeslicer`).
    data : array-like
        Field data.
    
    """
    def __init__(self, name, standard_name='', ndim=0, unit='', filename='',
                 timestamp='*/*/*/*', data=[]):
        self.name = str(name)
        self.standard_name = str(standard_name)
        self.ndim = int(ndim)
        self.unit = str(unit)
        self.filename = filename
        self.filepath = os.path.abspath(self.filename)
        self.timestamp = timestamp
        self.data = np.array(data)


#-----------------------------------------------------------------------------
# HEMCO API classes
#-----------------------------------------------------------------------------

class EmissionExt(object):
    """
    An extension of the Harvard Emissions Component (HEMCO).
    
    Parameters
    ----------
    name : string
        Descriptive extension name.
    enabled : bool
        True if the extension is enabled
    """
    def __init__(self, name, enabled=True):
        self._number = None      # not public, defined while loading/saving
                                 # emission settings
        self.name = str(name)
        self.enabled = bool(enabled)


class BaseEmissionField(BaseField):
    """
    A particular base emission field that can be used by HEMCO.
    
    Parameters
    ----------
    name : string
        Descriptive field name.
    species : string or :class:`globchem.Species` object
        Emitted species. If only the model name (id) is given, a new
        :class:`globchem.Species` object will be created.
    category : int
        Emission category. Fields of the same category will be assembled based
        upon hierarchies.
    hierarchy : int
        Emission hierarchy. Higher hierarchy emissions will overwrite lower
        hierarchy emissions (if same category).
    emission_ext : :class:`EmissionExt` object or None
        HEMCO extension to use with this emission field. Set None if the field
        is to be used by the HCMO core.
    scale_factors : list :class:`ScalarField` objects
        Scale factors to be applied to the base emission field.
    
    Other Parameters
    ----------------
    standard_name, ndim, unit, filename, timestamp, data
        See :class:`BaseField`.
    """
    
    def __init__(self, name, species, category, hierarchy,
                 emission_ext=None, scale_factors=[], **kwargs):
        super(BaseEmissionField, self).__init__(name, **kwargs)
        self.species = str(species)
        self.category = int(category)
        self.hierarchy = int(hierarchy)
        self.emission_ext = emission_ext
        self._scale_factors = ObjectCollection(ScalarField, scale_factors)
    
    @property
    def scale_factors(self):
        """
        Scale factors to be applied to the base emission field (collection
        of :class:`ScalarField` objects).
        
        See Also
        --------
        :class:`utils.data_struct.ObjectCollection`
        """
        return self._scale_factors


class ScalarField(BaseField):
    """
    A scale factor (or a mask field) that can be applied to any
    base emission field.
    
    Parameters
    ----------
    operator : {'mul', 'div', 'sqr'} or None
        Mathematical operator (multiply, divide or square)
    mask_window : [
        Give the approximate window of the mask field (Lon1/Lat1/Lon2/Lat2).
        Lon1/Lat1 denote the lower left corner, Lon2/Lat2 is the upper
        right corner.
    mirror : bool
        Invert the mask field (1-S)
    """
    def __init__(self, operator=None, mask_window=None, mirror=False,
                 **kwargs):
        self._id = None   # not public, defined while loading/saving
                          # emission settings
        self.operator = operator
        self.mask_window = mask_window
        self.mirror = bool(mirror)

        

class Emissions(object):
    """
    Global emission settings.
    
    Parameters
    ----------
    extensions : list of :class:`EmissionExt` objects
        HEMCO extensions.
    base_emissions : list of :class:`BaseEmissionField` objects
        Base emission fields.
    description : string
        A short description of emission settings.
    """
    def __init__(self, extensions=[], base_emissions=[], description=""):
        self._extensions = ObjectCollection(EmissionExt, extensions)
        self._base_emissions = ObjectCollection(BaseEmissionField,
                                                base_emissions)
        self.description = str(description)
    
    @property
    def extensions(self):
        """
        HEMCO extensions (collection of :class:`EmissionExt` objects).
        
        See Also
        --------
        :class:`utils.data_struct.ObjectCollection`
        """
        return self._extensions
    
    @property
    def base_emissions(self):
        """
        Base emission fields (collection of :class:`BaseEmissionField` objects).
        
        See Also
        --------
        :class:`utils.data_struct.ObjectCollection`
        """
        return self._base_emissions
    
    @property
    def scale_factors(self):
        """
        All scale factors that are attached to the base emission fields.
        
        Returns a list of :class:`ScalarField` objects (if a scale factor is
        attached to several emission fields, it appears only once in the list).
        """
        scale_factors = []
        for field in self.base_emissions:
            scale_factors.extend(field.scale_factors)
        #scale_factors = ObjectCollection(ScalarField, set(scale_factors))
        #return scale_factors.sort('_id')._list
        return list(set(scale_factors))
    
    @classmethod
    def load(cls, filename):
        """
        Load emission settings from an HEMCO-formatted input file given by
        `filename`.
        
        See Also
        --------
        :func:`load_emissions_file`
        """
        pass
    
    @classmethod
    def builtin(cls, settings):
        """
        Load built-in emission settings.
        
        See Also
        --------
        :func:`load_emissions_builtin`
        """
        settings_file = os.path.join(BUILTIN_SETTINGS_PATH, settings)
        return cls.load(settings_file)
    
    def save(self, filename, **kwargs):
        """
        Save emission settings to an HEMCO-formatted input file given by
        `filename`.
        
        Other Parameters (kwargs)
        -------------------------
        verbose : bool
            Run HEMCO in verbose mode (default: False).
        """
        # reset ids of scale factors
        inc = 0
        for sf in self.scale_factors:
            sf._id = inc
            inc += 1
        
        # reset extension numbers
        inc = 101
        for ext in self.extensions:
            ext._number = inc
            inc += 1
        
        
    
    def compute_emissions(self, time, grid):
        """
        Call here the Python-wrapped FORTRAN routine to calculate emissions
        at particular time(s) and with a given grid.
        """
        pass


#-----------------------------------------------------------------------------
# HEMCO API functions
#-----------------------------------------------------------------------------

def load_emissions_file(filename):
    """
    Load emission settings from a file.
    
    Parameters
    ----------
    filename : string
        Name of (path to) the HEMCO settings file.
    
    Returns
    -------
    A :class:`Emissions` object.
    """
    return Emissions.load(filename)


def load_emissions_builtin(settings):
    """
    Load built-in emission settings
    
    Parameters
    ----------
    settings : string
        Name of the built-in settings (see below).
    
    Returns
    -------
    A :class:`Emissions` object.
    
    Available Settings
    ------------------
    'all'
        Contains all HEMCO extensions, base emission fields, scale factors and
        masks available in GEOS-Chem.
    'standard'
        Standard settings
    'another_preset'
        Another preset...
    """
    return Emissions.builtin(settings)
