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
import sys
from copy import copy, deepcopy
import numpy as np

from pyhemco.timetools import strp_datetimeslicer
from pyhemco.datatypes import ObjectCollection
from pyhemco.io import read_config_file, write_config_file

BUILTIN_SETTINGS_PATH = 'path/to/default/settings/files'
BEF_ATTR_NAME = 'emission_base'
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
    var_name : string
        Field (variable) name.
    ndim : int
        Data (number of) dimensions 
    unit : string
        Unit of data.
    filename : string
        Filename or path to the file where data is stored.
    data : array-like
        Field data.
    
    """

    def __init__(self, name, var_name='', ndim=0, unit='',
                 filename='', data=None, **kwargs):
        data = data or []
        if isinstance(ndim,str):
            if ndim=='xy':
                ndim=2
            elif ndim=='xyz':
                ndim=3
            else:
                raise ValueError("unsupported ndim character:",ndim)

        self.name = str(name)
        self.var_name = str(var_name)
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


    def is_base(self):
        """Returns True if this is a base field."""
        isbase = False
        if BEF_ATTR_NAME in self.attributes.keys():
            isbase = True
        return isbase

    def is_scal(self):
        """Returns True if this is a scale factor field."""
        isscal = False
        if SF_ATTR_NAME in self.attributes.keys():
            isscal = True
        return isscal
               
    def is_mask(self):
        """Returns True if this is a mask field."""
        ismask = False
        if SF_ATTR_NAME in self.attributes.keys():
            ismask = 'mask_window' in self.attributes[SF_ATTR_NAME].keys()
        return ismask
        
    def __str__(self):
        return 'GCField {}'.format(self.name or self.var_name)

    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__,
                                   self.name or self.var_name)


#-----------------------------------------------------------------------------
# HEMCO API classes and functions
#-----------------------------------------------------------------------------

def _add_emission_attr(gc_field, name, attr_name, attr_val, copy_field):
    """
    Adds an emission-specific attribute to `gc_field` (raises an error if
    such an attribute is already set for `gc_field`).
    """
    e_attrs = (BEF_ATTR_NAME, SF_ATTR_NAME)
    f_attrs = gc_field.attributes.keys()
    if any(a in f_attrs for a in e_attrs):
        # TODO: raise custom Exception (for example 'InvalidFieldException')
        raise ValueError("gc_field has already an emission attribute")

    if copy_field:
        e_field = gc_field.copy(copy_data=True)
        e_field.name = str(name)
    else:
        e_field = gc_field
    e_field.attributes[attr_name] = attr_val

    return e_field

def is_base_emission_field(gc_field, critical=False):
    """
    Check whether `gc_field` (a :class:`GCField` object) has base emission
    field metadata.

    Will raise an error if `critical` is True and no base emission attribute
    is found.
    """
    etest = bool(gc_field.attributes.get(BEF_ATTR_NAME, False))
    if critical and not etest:
        # TODO: raise custom exception like InvalidFieldError
        raise ValueError("missing '{}' attribute".format(BEF_ATTR_NAME))
    else:
        return etest


def is_scale_factor(gc_field, critical=False):
    """
    Check if `gc_field` (a :class:`GCField` object) has scale factor or
    mask metadata.

    Will raise an error if `critical` is True and no scale factor attribute
    is found.
    """
    etest = bool(gc_field.attributes.get(SF_ATTR_NAME, False))
    if critical and not etest:
        # TODO: raise custom exception like InvalidFieldError
        raise ValueError("missing '{}' attribute".format(SF_ATTR_NAME))
    else:
        return etest
        

def base_emission_field(gc_field, name, timestamp, species, category,
                        hierarchy, scale_factors=None, copy=False):

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
    scale_factors : list :class:`GCField` objects
        Scale factors and masks to be applied to the base emission field.
        Each field in the list must have a 'emission_scale_factor' attribute.
    copy : bool
        Copy `gc_field` (True) or modifying it in place.
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new field attribute 'emission_base'.
        An extra class attribute `emission_scale_factors` is also added
        for quick access to scale factors assigned to this field.
    
    """
    scale_factors    = scale_factors or []

    fpost_add = lambda gcf: is_scale_factor(gcf, critical=True)
    scale_factors = ObjectCollection(scale_factors, ref_class=GCField,
                                     fpost=(fpost_add, None))

    e_attr = {'name': str(name),
              'timestamp': str(strp_datetimeslicer(timestamp)),
              'species': species,
              'category': int(category),
              'hierarchy': int(hierarchy),
              'scale_factors': scale_factors}

    e_field = _add_emission_attr(gc_field, name, BEF_ATTR_NAME,
                                 e_attr, copy)

    # shortcut for scale factors
    e_field.emission_scale_factors = scale_factors

    if copy:
        return e_field


def scale_factor(gc_field, name, timestamp, operator='*', copy=False,
                 fid=None):
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
    operator : {'*', '/', '**2'}
        Mathematical operator (multiply, divide or square)
    copy : bool
        Copy `gc_field` (True) or modifying it in place.
    fid : int or None
        Specify manually an ID to identify the scale factor (if None, an ID
        will be further set automatically).
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new attribute 'emission_scale_factor'.
    
    """
    if fid is not None:
        fid = int(fid)

    sf_attr = {'name': str(name),
               'timestamp': str(strp_datetimeslicer(timestamp)),
               'operator': operator,
               'fid': fid}

    e_field = _add_emission_attr(gc_field, name, SF_ATTR_NAME,
                                 sf_attr, copy)
    if copy:
        return e_field


def mask(gc_field, name, timestamp, mask_window=None, mirror=False,
         copy=False, fid=None):
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
    fid : int or None
        Specify manually an ID to identify the mask (if None, an ID
        will be further set automatically).
    
    Returns
    -------
    :class:`GCField` object
        (a copy of) `gc_field` with a new attribute 'emission_scale_factor'.
    
    """
    if fid is not None:
        fid = int(fid)

    sf_attr = {'name': str(name),
               'timestamp': str(strp_datetimeslicer(timestamp)),
               'operator': 'mul',
               'mask_window': mask_window,
               'mirror': bool(mirror),
               'fid': fid}

    e_field = _add_emission_attr(gc_field, name, SF_ATTR_NAME,
                                 sf_attr, copy)
    if copy:
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
    base_emission_fields : iterable or None
        List of base emission fields (i.e., :class:`GCField` objects that have
        a specific 'emission_base' field attribute) that will be used by the
        extension.
    eid : int or None
        Specify manually an ID to identify the extension. Note that 0
        corresponds to HEMCO Core.
    """

    def __init__(self, name, enabled=True, base_emission_fields=None,
                 eid=None, species=[], **kwargs):
        if eid is not None:
            eid = int(eid)
        base_emission_fields = base_emission_fields or []
        is_bef = lambda gcfield: is_base_emission_field(gcfield, critical=True)

        self.eid = eid
        self.name = str(name)
        self.enabled = bool(enabled)
        self.species = species
        self._base_emission_fields = ObjectCollection(base_emission_fields,
                                                      ref_class=GCField,
                                                      fpre=(is_bef, None))
        self.settings = dict()
        self.settings.update(kwargs)

    def addSetting(self,setting_name,setting_val):
        self.settings[setting_name] = setting_val

    @property
    def base_emission_fields(self):
        """
        Base emission fields.

        Returns
        -------
        A collection (:class:`datatypes.ObjectCollection`) of
        base emission fields (i.e., :class:`GCField` objects that have a
        specific 'emission_base' field attribute).

        See Also
        --------
        :func:`base_emission_field`
        """
        return self._base_emission_fields

    def __str__(self):
        return "GC-Emission extension '{0}' ({1})" \
            .format(self.name, str(self.eid))

    def __repr__(self):
        return '<{0}: {1} ({2})>'.format(self.__class__.__name__,
                                         self.name,
                                         str(self.eid))


class Emissions(object):
    """
    Global emission settings.
    
    Parameters
    ----------
    extensions : list of :class:`EmissionExt` objects
        HEMCO extensions (must include HEMCO Core).
        Each extension can have base emission fields and each
        base emission field can have scale factors and masks.
    description : string
        A short description of emission settings.

    See Also
    --------
    :class:`EmissionExt`
    :func:`base_emission_field`
    :func:`scale_factor`

    """

    def __init__(self, extensions=[], description=""):
        self._extensions = ObjectCollection(extensions, ref_class=EmissionExt)
        self.description = str(description)
        self.name = str(self.description)

    @property
    def extensions(self):
        """
        HEMCO extensions.

        Returns
        -------
        A collection (:class:`datatypes.ObjectCollection`) of extensions
        (:class:`EmissionExt` objects) including HEMCO Core.
        """
        return self._extensions

    @property
    def base_emission_fields(self):
        """
        Base emission fields.

        Returns
        -------
        A read-only collection (:class:`datatypes.ObjectCollection`) of
        base emission fields (i.e., :class:`GCField` objects that have a
        specific 'emission_base' field attribute).
        If a field is attached to several extensions, it appears only once
        in the collection.
        
        See Also
        --------
        :func:`base_emission_field`
        """
        bef = []
        for ext in self.extensions:
            bef.extend(ext.base_emission_fields._list)
        return ObjectCollection(set(bef), ref_class=GCField, read_only=True)

    @property
    def scale_factors(self):
        """
        Scale factors and masks.

        Returns
        -------
        A read-only collection (:class:`datatypes.ObjectCollection`) of
        scale factors and masks (i.e., :class:`GCField` objects that have a
        specific 'emission_scale_factor' field attribute).
        If a scale factor is attached to several base emission fields, it
        appears only once in the collection.

        See Also
        --------
        :func:`scale_factor`
        """
        scale_factors = []
        for field in self.base_emission_fields:
            e_attr = field.attributes['emission_base']
            e_sf_list = e_attr.get('scale_factors', [])
            scale_factors.extend(e_sf_list)
        return ObjectCollection(set(scale_factors), ref_class=GCField,
                                read_only=True)

    def get_scalIDs(self):
        """
        Return a list of all currently defined scale factor IDs.
        """
        fids = [sf.attributes[SF_ATTR_NAME].get('fid')
                for sf in self.scale_factors]
        return fids

    def check_id(self):
        """
        Check scale factors and extensions identifiants
        (missing ids or duplicates).
        """
        fids = self.get_scalIDs()
        if None in fids or len(set(fids)) != len(fids):
            # TODO: raise custom exception
            raise ValueError("Missing or duplicate scale factor fid")

        eids = [ext.eid for ext in self.extensions]
        if None in eids or len(set(eids)) != len(eids):
            # TODO: raise custom exception
            raise ValueError("Missing or duplicate extension eid")
        if 0 not in eids:
            # TODO: raise custom exception
            raise ValueError("HEMCO Core (eid=0) not found in extensions")

    def resolve_id(self):
        """
        Automatically resolve scale factors and extensions ID conficts
        (add new ID(s) if not already set, update ID(s) if needed).
        """
        fids = self.get_scalIDs()
        min_fid = min(i for i in fids if i is not None)
        range_fids = range(min_fid, max(fids) + len(fids) + 1)
        duplicate_fids = set([fid for fid in fids if fids.count(fid) > 1])
        available_fids = sorted(set(range_fids) - set(fids))

        inc = 0
        first_dups = []
        for sf in self.scale_factors:
            fid = sf.attributes[SF_ATTR_NAME].get('fid')
            if fid not in duplicate_fids and fid is not None:
                continue
            if fid not in first_dups and fid is not None:
                first_dups.append(fid)
                continue
            sf.attributes[SF_ATTR_NAME]['fid'] = available_fids[inc]
            inc += 1

        eids = [ext.eid for ext in self.extensions]
        min_eid = min(i for i in eids if i is not None)
        range_eids = range(min_eid, max(eids) + len(eids) + 1)
        duplicate_eids = set([eid for eid in eids if eids.count(eid) > 1])
        available_eids = sorted(set(range_eids) - set(eids))

        inc = 0
        first_dups = []
        for ext in self.extensions:
            eid = ext.eid
            if eid not in duplicate_eids and eid is not None:
                continue
            if eid not in first_dups and eid is not None:
                first_dups.append(eid)
                continue
            ext.eid = available_eids[inc]
            inc += 1

    @classmethod
    def load(cls, filename):
        """
        Load emission settings from an HEMCO-formatted input file given by
        `filename`.
        
        See Also
        --------
        :func:`load_emissions_file`
        """        
        cls = read_config_file( filename )
        return cls

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

    def save(self, filename, resolve_id=False):
        """
        Save emission settings to an HEMCO-formatted input file given by
        `filename`.
        """
        # TODO: (not yet implemented)
        if resolve_id:
            self.resolve_id()
        else:
            self.check_id()
            
        write_config_file ( self, filename )

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

    def __str__(self):
        return "GC-Emission settings: {0}".format(self.description)

    def __repr__(self):
        return repr(self)

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
