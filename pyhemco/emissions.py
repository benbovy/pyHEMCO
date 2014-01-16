# -*- coding: utf-8 -*-

# part of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2013 Benoit Bovy
# see license.txt for more details
# 
#

"""
A Python API for the Harvard Emissions Component (HEMCO) of GEOS-Chem.

Not yet operational.

"""

import os
from copy import copy, deepcopy

import numpy as np

from pyhemco.timetools import strp_datetimeslicer
from pyhemco.datatypes import ObjectCollection


BUILTIN_SETTINGS_PATH = 'path/to/default/settings/files'
BASE_EM_ATTR_NAME = 'emission_base'
SF_ATTR_NAME = 'emission_scale_factor'


#-----------------------------------------------------------------------------
# Generic classes or functions (not part of the public HEMCO API)
# will be replaced or moved elsewhere.
#-----------------------------------------------------------------------------


class GCField(object):
    """
    A GEOS-Chem data field.
    
    Parameters
    ----------
    name : string
        Field descriptive name
    standard_name : string
        Field (variable) standard name.
    ndim : int
        Data (number of) dimensions 
    unit : string
        Unit of data.
    filename : string
        Filename or path to the file where data is stored.
    data : array-like
        Field data.
    
    """
    def __init__(self, name, standard_name='', ndim=0, unit='',
                 filename='', data=[], **kwargs):
        self.name = str(name)
        self.standard_name = str(standard_name)
        self.ndim = int(ndim)
        self.unit = str(unit)
        self.filename = filename
        self.filepath = os.path.abspath(self.filename)
        self.data = np.array(data)
        self.attributes = dict()
        self.attributes.update(kwargs)
    
    def copy(self, copy_data=False):
        """Return a new copy of the Field."""
        if copy_data:
            return deepcopy(self)
        else:
            return copy(self)
    
    def __str__(self):
        # TODO:
        pass
    
    def __repr__(self):
        # TODO:
        pass


#-----------------------------------------------------------------------------
# HEMCO API classes and functions
#-----------------------------------------------------------------------------

def _add_emission_attr(gc_field, name, attr_name, attr_val, copy):
    """
    Adds an emission-specific attribute to `gc_field` (raises an error if
    such an attribute is already set for `gc_field`).
    """
    e_attrs = (BASE_EM_ATTR_NAME, SF_ATTR_NAME)
    f_attrs = gc_field.attributes.keys()
    if any(a in f_attrs for a in e_attrs):
        # TODO: raise custom Exception (for example 'InvalidFieldException')
        raise ValueError("gc_field has already an emission attribute")
    
    if copy:
        e_field = gc_field.copy()
        e_field.name = str(name)
    else:
        e_field = gc_field
    e_field.attributes[attr_name] = attr_val
    
    return e_field


def base_emission_field(gc_field, name, timestamp, species, category,
                        hierarchy, extension=None, scale_factors=[],
                        copy=False):
    """
    Create a base emission field from an existing GEOS-Chem field.
    
    Parameters
    ----------
    gc_field : :class:`GCField` object.
        The GEOS-Chem field.
    name : string
        Descriptive emission field name.
    timestamp : string
        time stamp of interest (YYYY/MM/DD/HH).
        See :func:`timetools.strptimeslicer`.
    species : string or :class:`globchem.Species` object
        Emitted species. If only the model name (id) is given, a new
        :class:`globchem.Species` object will be created.
    category : int
        Emission category. Fields of the same category will be assembled based
        upon hierarchies.
    hierarchy : int
        Emission hierarchy. Higher hierarchy emissions will overwrite lower
        hierarchy emissions (if same category).
    extension : :class:`EmissionExt` object or None
        HEMCO extension to use with this emission field. Set None if the field
        is to be used by the HCMO core.
    scale_factors : list :class:`GCField` objects
        Scale factors to be applied to the base emission field. Each field in
        the list must have a 'emission_scale_factor' attribute.
    copy : bool
        Copy `gc_field` (True) or modifying it in place.
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new attribute 'emission_base'.
    
    """
    e_attr = {'name': str(name),
              'timestamp': str(strp_datetimeslicer(timestamp)),
              'species': species,
              'category': int(category),
              'hierarchy': int(hierarchy),
              'extension': extension,
              'scale_factors': scale_factors}
    
    e_field = _add_emission_attr(gc_field, name, BASE_EM_ATTR_NAME,
                                 e_attr, copy)
    return e_field


def scale_factor(gc_field, name, timestamp, operator='mul', copy=False):
    """
    Create an emission scale factor from an existing GEOS-Chem field.
    
    Parameters
    ----------
    gc_field : :class:`GCField` object.
        The GEOS-Chem field.
    name : string
        Descriptive field name.
    timestamp : string
        time stamp of interest (YYYY/MM/DD/HH).
        See :func:`timetools.strptimeslicer`.
    operator : {'mul', 'div', 'sqr'}
        Mathematical operator (multiply, divide or square)
    copy : bool
        Copy `gc_field` (True) or modifying it in place.
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new attribute 'emission_scale_factor'.
    
    """
    sf_attr = {'name': str(name),
               'timestamp': str(strp_datetimeslicer(timestamp)),
               'operator': operator}
    
    e_field = _add_emission_attr(gc_field, name, SF_ATTR_NAME,
                                 sf_attr, copy)
    return e_field


def mask(gc_field, name, timestamp, mask_window=None, mirror=False,
         copy=False):
    """
    Create an emission mask from an existing GEOS-Chem field.
    
    Parameters
    ----------
    gc_field : :class:`GCField` object.
        The GEOS-Chem field.
    name : string
        Descriptive field name.
    timestamp : string
        time stamp of interest (YYYY/MM/DD/HH).
        See :func:`timetools.strptimeslicer`.
    mask_window : [int, int, int, int] or None
        An approximate window for the mask field (Lon1/Lat1/Lon2/Lat2).
        Lon1/Lat1 denote the lower left corner, Lon2/Lat2 is the upper
        right corner.
    mirror : bool
        Invert the mask field (1-S).
    copy : bool
        Modify `gc_field` in place (False, default), or return a new copy.
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new attribute 'emission_scale_factor'.
    
    """
    sf_attr = {'name': str(name),
               'timestamp': str(strp_datetimeslicer(timestamp)),
               'operator': 'mul',
               'mask_window': mask_window,
               'mirror': bool(mirror)}
    e_field = _add_emission_attr(gc_field, name, SF_ATTR_NAME,
                                 sf_attr, copy)
    return e_field
    

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


class Emissions(object):
    """
    Global emission settings.
    
    Parameters
    ----------
    extensions : list of :class:`EmissionExt` objects
        HEMCO extensions.
    base_emission_fields : list of :class:`GCField` objects
        Base emission fields.
    description : string
        A short description of emission settings.
    
    Other Parameters
    ----------------
    verbose : bool
        Run HEMCO in verbose mode (default: False).
    **kwargs
        Specify any additional settings by name=value.
    """
    def __init__(self, extensions=[], base_emission_fields=[], description="",
                 **kwargs):
        self._extensions = ObjectCollection(EmissionExt, extensions)
        self._base_emission_fields = ObjectCollection(GCField,
                                                      base_emission_fields)
        self.description = str(description)
        self.settings = kwargs
    
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
    def base_emission_fields(self):
        """
        Base emission fields (collection of :class:`BaseEmissionField` objects).
        
        See Also
        --------
        :class:`utils.data_struct.ObjectCollection`
        """
        return self._base_emission_fields
    
    @property
    def scale_factors(self):
        """
        All scale factors (and masks) that are attached to the base emission
        fields.
        
        It is a read-only collection of :class:`GCField` objects (if a scale
        factor is attached to several emission fields, it appears only once
        in the collection).
        """
        scale_factors = []
        for field in self.base_emission_fields:
            e_attr = field.attributes['emission_base']
            e_sf_list = e_attr.get('emission_scale_factors', [])
            scale_factors.extend(e_sf_list)
        return ObjectCollection(GCField, set(scale_factors), read_only=True)
    
    @classmethod
    def load(cls, filename):
        """
        Load emission settings from an HEMCO-formatted input file given by
        `filename`.
        
        See Also
        --------
        :func:`load_emissions_file`
        """
        # TODO: (not yet implemented)
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
    
    def save(self, filename):
        """
        Save emission settings to an HEMCO-formatted input file given by
        `filename`.
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
        
        # TODO: (not yet implemented)
    
    def compute_emissions(self, time, grid):
        """
        Call here the Python-wrapped FORTRAN routine to calculate emissions
        at particular time(s) and with a given grid.
        
        Returns
        -------
        :class:`GCField` object
        """
        # TODO: (not yet implemented)
        pass
        

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
