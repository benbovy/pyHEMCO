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
    Check whether `gc_field` (a :class:`GCField` object) has scale factor or
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
                        hierarchy, extension=None, scale_factors=None,
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
    scale_factors = scale_factors or []

    fpost_add = lambda gcf: is_scale_factor(gcf, critical=True)
    scale_factors = ObjectCollection(scale_factors, ref_class=GCField,
                                     fpost=(fpost_add, None))

    e_attr = {'name': str(name),
              'timestamp': str(strp_datetimeslicer(timestamp)),
              'species': species,
              'category': int(category),
              'hierarchy': int(hierarchy),
              'extension': extension,
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
    eid : int or None
        Specify manually an ID to identify the extension.
    """

    def __init__(self, name, enabled=True, eid=None):
        if eid is not None:
            eid = int(eid)
        self.eid = eid
        self.name = str(name)
        self.enabled = bool(enabled)

    def __str__(self):
        return "GC-Emission extension '{0}' ({1})" \
            .format(self.name, str(self.eid or 'no-id'))

    def __repr__(self):
        return '<{0}: {1} ({2})>'.format(self.__class__.__name__,
                                         self.name,
                                         str(self.eid or 'no-id'))


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
    extra_settings : dict or None
        Additional settings of HEMCO.

    """

    def __init__(self, base_emission_fields, description="",
                 extra_settings=None):
        extra_settings = extra_settings or {}

        self._extensions = ObjectCollection(
            [],
            ref_class=EmissionExt,
            fpre=(self._fpre_add_ext, self._fpre_remove_ext),
            fpost=(None, None))

        self._base_emission_fields = ObjectCollection(
            base_emission_fields,
            ref_class=GCField,
            fpre=(self._fpre_add_bef, None),
            fpost=(self._fpost_add_bef, None))

        self.description = str(description)
        self.extra_settings = dict(extra_settings)

    def _fpre_add_bef(self, gcfield):
        """
        Before adding a gcfield as a base emission field, check the gcfield
        attributes.
        """
        return is_base_emission_field(gcfield, critical=True)

    def _fpost_add_bef(self, bef):
        """
        After added a base emission field, add its assigned extension to
        the emission setup (if needed).
        """
        bef_ext = bef[BEF_ATTR_NAME]['extension']
        if bef_ext not in self._extensions:
            self._extensions.add(bef_ext)

    # def _fpost_remove_bef(self, bef):
    #     """
    #     After removed a base emission field, (eventually) remove its assigned
    #     extension from the emission setup.
    #     """
    #     bef_ext = lambda ext: ext == bef[BEF_ATTR_NAME]['extension']
    #     self._extensions.get(bef_ext).remove()

    def _fpre_add_ext(self, ext):
        """
        Check if the extension has been already added to the emission setup.
        """
        try:
            comp_ext = self._extensions.get_object(name=ext.name)
            if comp_ext != ext:
                raise ValueError("found the same {} extension with other "
                                 "settings".format(ext.name))
            else:
                return False
        except ValueError:
            return True

    def _fpre_remove_ext(self, ext):
        """
        Cannot remove an extension which involves at least one base emission
        field.
        """
        bef_exts = [bef[BEF_ATTR_NAME]['extension']
                    for bef in self._base_emission_fields]
        if ext in bef_exts:
            raise ValueError("Can not remove an extension that is referenced "
                             "by at least one emission field")

    @property
    def base_emission_fields(self):
        """
        Base emission fields (collection of :class:`GCField` objects with a
        specific 'emission_base' extra attribute).
        
        See Also
        --------
        :class:`datatypes.ObjectCollection`
        :func:`base_emission_field`
        """
        return self._base_emission_fields

    @property
    def scale_factors(self):
        """
        All scale factors (and masks) that are attached to the base emission
        fields.
        
        Return a collection of :class:`GCField` objects (if a scale
        factor is attached to several emission fields, it appears only once
        in the list).
        """
        scale_factors = []
        for field in self.base_emission_fields:
            e_attr = field.attributes['emission_base']
            e_sf_list = e_attr.get('scale_factors', [])
            scale_factors.extend(e_sf_list)
        return ObjectCollection(set(scale_factors), ref_class=GCField,
                                read_only=True)

    @property
    def extensions(self):
        """
        HEMCO extensions (list of :class:`EmissionExt` objects).

        Return a collection of :class:`EmissionExt` objects (if an extension
        is attached to several emission fields, it appears only once
        in the list). HEMCO Core is not included in the list.
        """
        return self._extensions

    def check_id(self):
        """
        Check scale factors and extensions identifiants
        (missing ids or duplicates).
        """
        fids = [sf.attributes[SF_ATTR_NAME].get('fid')
                for sf in self.scale_factors]
        if None in fids or len(set(fids)) != len(fids):
            # TODO: raise custom exception
            raise ValueError("Missing or duplicate scale factor ID(s)")

        eids = [ext.eid for ext in self.extensions]
        if None in eids or len(set(eids)) != len(eids):
            # TODO: raise custom exception
            raise ValueError("Missing or duplicate extension ID(s)")

    def resolve_id(self):
        """
        Automatically resolve scale factors and extensions ID conficts
        (add new ID(s) if not already set, update ID(s) if needed).
        """
        fids = [sf.attributes[SF_ATTR_NAME].get('fid')
                for sf in self.scale_factors]
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
