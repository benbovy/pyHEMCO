# -*- coding: utf-8 -*-

# parts of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2012-2013 Benoît Bovy
# see license.txt for more details
# 

"""
Input/Ouput reading/writing...
"""


def strlist_to_fields(raw_vals, fields_spec, none_val=None):
    """
    Get fields from a list of strings, given fields specification.
    
    Parameters
    ----------
    raw_vals : [string, string, ...]
        Values of fields that have to be convert to the correct type.
    fields_spec : ((string, callable), (string, callable), ...)
        Sequence of 2-length tuples (name, type) defining the name
        and type - or any callable that return the expected type - for each
        field.
    none_val : string or other
        Identifies a None value in raw_vals.
    
    Returns
    -------
    tuple of 2-length tuples
        (field name, field value).
    
    """
    fields = []
    for val, spec in zip(raw_vals, field_spec):
        fname, ftype = spec
        if val == none_val:
            fields.append((fname, None))
        else:
            fields.append((fname, ftype(val)))
    return tuple(fields)


def fields_to_strlist(fields, none_str=''):
    """
    Set a list of strings, given fields specification.
    
    Parameters
    ----------
    fields : ((string, val, callable), (string, val, callable), ...)
        (value, formatter) for each field. Formatter is a callable for
        converting the field value to a string. 
    none_str : string
        None value format.
    
    Returns
    -------
    list of fields values as strings.
    
    """
    return [ffmt(fval) if fval is not None else none_str
            for fval, ffmt in fields]

