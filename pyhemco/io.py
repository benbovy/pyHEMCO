# -*- coding: utf-8 -*-

# parts of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2012-2013 Benoît Bovy
# see license.txt for more details
# 

"""
Several input/output writing routines for pyHEMCO.
"""

import sys
import pyhemco

SEPARATOR = '####################################################################################'
COMMENT = '#'

#-----------------------------------------------------------------------------
# HEMCO I/O functions
#-----------------------------------------------------------------------------

def find_substr_index( strings, substring ):
    """
    Returns the index of the given substring in a list of strings. Raises an
    error if none or more than one matching list elements are found.    
    """
    idx = [i for i, string in enumerate(strings) if substring in string]
    if len(idx) != 1:
        msg="Pattern " + substring + " is not of length one!"
        raise ValueError(msg)
    return idx[0]

def config_line_split( line, expLen=0, sep=' ' ):
    """
    Wrapper function to split line 'line' of the configuration file into substrings.
    Arg 'sep' identified the substring separator character, and 'expLen' denotes 
    the expected number of substrings and can be set to provide an error check on 
    the passed line.
    """
    if line[0] == COMMENT:
        spl = []
    else:
        iline = line.replace('\t',' ')
        spl   = iline.split(sep)
        spl   = [x.strip() for x in spl if x !='']
        
        if (expLen > 0) and (len(spl) != expLen):
            msg = "Line " + line + " has not " + str(expLen) + " substrings!"
            raise ValueError(msg)       
    return spl

def read_config_file( filename, description='' ):
    """
    Reads emissions information from file 'filename' and saves it into an 
    emissions class object ('emis_setup').
    
    Parameters
    ----------
    filename : (string)
        File name (full path) of HEMCO configuration file
    description : (string)
        Setup description

    Returns
    ----------
    emis_setup : :class:`Emissions` object.
        Emissions setup object

    History
    ----------
    20140217 ckeller: Initial version    
    """
    
    # create blank setup
    emis_setup = pyhemco.emissions.Emissions( [], description=description )
    
    # open file
    cfg_lines = [line.rstrip('\n') for line in open(filename) if line.strip()]
        
    # read settings
    read_settings( emis_setup, cfg_lines )
    read_base_emissions( emis_setup, cfg_lines )
    read_extensions( emis_setup, cfg_lines, read_all=True)
    
    return emis_setup

def write_config_file( emis_setup, filename, style='HEMCO' ):
    """
    Write emission setup into file for re-use later on.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be written into file).
    filename : (string)
        File name (full path) of HEMCO configuration file
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version
    
    TODO: Add ESMF writing capability.
    """
    
    # open file
    outfile = open( filename, 'w' )
    outfile.write('### HEMCO INPUT FILE ###\n')
    outfile.write(' \n')
        
    # write file
    write_settings( emis_setup, outfile, style )
    write_base_emissions ( emis_setup, outfile, style )
    write_scale_factors ( emis_setup, outfile, style )
    write_masks ( emis_setup, outfile, style )
    write_extensions( emis_setup, outfile, style )
    
    # close file
    outfile.write('### END OF HEMCO INPUT FILE ###\n')
    outfile.close()

def read_settings( emis_setup, cfg_lines, 
                   start="BEGIN SECTION SETTINGS", end="END SECTION SETTINGS" ):
    """
    Extracts the emission settings from cfg_lines and saves them into  
    emissions class object ('emis_setup').
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be created & filled).
    cfg_lines : [character]
        List of configuration file lines
    start : [character]
        Start scanning file from this line
    end : [character]
        Scan file up to this line

    History
    ----------
    20140217 ckeller: Initial version    
    """    
     
    # identify start of settings section 
    idx = find_substr_index( cfg_lines, start)
    eof = len(cfg_lines)-1
    
    # read settings and add to emis_setup until end of settings reached. 
    idx = idx+1
    while True:

        # exit loop?
        if idx > eof:
            break
        if end in cfg_lines[idx]:
            break        
 
        # split line
        spl = config_line_split( cfg_lines[idx], sep=':', expLen=2)
        
        # empty list = this line is a comment
        if len(spl) == 0:
            idx=idx+1
            continue
            
        # now extract values
        dctname = spl[0].strip(':')
        dctval  = spl[1]
        
        # autodetect true/false
        if dctval.lower()=='true':
            dctval=True
        elif dctval.lower()=='false':
            dctval=False
        
        # add to emis_setup extra_settings dictionary
        emis_setup.extra_settings.update({dctname: dctval})
        
        # increase index
        idx = idx+1

def read_base_emissions( emis_setup, cfg_lines,
                         start="BEGIN SECTION BASE EMISSIONS", end="END SECTION BASE EMISSIONS",
                         extension=None, read_all=False ):
    """
    Extracts the base emissions from cfg_lines and saves them into  
    emissions class object ('emis_setup'). If an extension is given, only the base
    emission fields belonging to this particular extension are read. 
    If an extension is given and read_all is set to False, only those base fields 
    are read that (a) belong to the given extension and (b) whose species name is listed
    as valid extension species.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be created & filled).
    cfg_lines : [character]
        List of configuration file lines
    start : [character]
        Start scanning file from this line
    end : [character]
        Scan file up to this line
    extension: :class:`EmissionExt` object or None
        Only read fields belonging to this extension
    read_all : bool
        If False, reads only fields whose extension ID and species name match
        the extension entries.

    History
    ----------
    20140217 ckeller: Initial version    
    """   
    
    # identify start of settings section 
    idx = find_substr_index( cfg_lines, start)
    eof = len(cfg_lines)-1
    
    # read settings and add to emis_setup until end of settings reached. 
    idx = idx+1
    while True:
        
        # exit loop?
        if idx > eof:
            break
        if end in cfg_lines[idx]:
            break        
        
        # split line
        spl = config_line_split( cfg_lines[idx], expLen=11 )
        
        # empty list = this line is a comment
        if len(spl) == 0:
            idx=idx+1
            continue
         
        # extract values
        eid     = int(spl[0])
        fldname = str(spl[1])
        srcfile = str(spl[2])
        srcvar  = str(spl[3])
        srctime = str(spl[4])
        srcdim  = str(spl[5])
        srcunit = str(spl[6])
        modspc  = str(spl[7])
 
        # For extensions, only consider data if it has the correct ExtNr and species ID!
        if extension is not None:
            if int(spl[0]) != extension.eid: 
                idx=idx+1
                continue
            if not read_all and modspc not in extension.species:
                idx=idx+1
                continue
        
        if str(spl[8]) == "-":
            scalIDs = []
        else:
            scalIDs = [int(x) for x in spl[8].split('/')]
        cat     = spl[9]
        hier    = spl[10]
        
        # eventually extract scale factors from file
        if srcvar == "-":
            data = [float(x) for x in srcfile.split('/')]
            srcfile = '-'
        else:
            data = []
            
        # default srctime:
        if srctime == "-":
            srctime = "*/*/*/*"
                    
        # add field information, incl. metadata and scale factor ids
        basefld = pyhemco.emissions.GCField(fldname,
                                            filename=srcfile,
                                            var_name=srcvar,
                                            unit=srcunit,
                                            ndim=srcdim,
                                            data=data )        
        pyhemco.emissions.base_emission_field(basefld, basefld.name, srctime, 
                                              modspc, cat, hier, extension=extension)
 
        # add to the setup
        emis_setup.base_emission_fields.add(basefld)
                
        # add/link scale factors scalIDs
        fids = emis_setup.get_scalIDs()
        
        # link each scalID with the base field
        for thisID in scalIDs:    

            # eventually read scale factor
            if thisID not in fids:
                scalfield = get_scale_factor ( cfg_lines, scalID=thisID )
                
                if scalfield is None:
                    scalfield = get_scale_factor ( cfg_lines, scalID=thisID, start="BEGIN SECTION MASKS", 
                                                   end="END SECTION MASKS", isMask=True )
                    
                if scalfield is None:
                    msg='Cannot get scale factor with ID ' + str(thisID)
                    raise ValueError(msg) 
            else:                
                filter_scal = lambda field: field.attributes['emission_scale_factor']['fid'] == thisID
                scalfield = emis_setup.scale_factors.filter(filter_scal).get_object()
            
            basefld.emission_scale_factors.add(scalfield)
            
        # increase line index
        idx = idx+1
        
def get_scale_factor( cfg_lines, scalID, start="BEGIN SECTION SCALE FACTORS", 
                      end="END SECTION SCALE FACTORS", isMask=False ):
    """
    Returns a GCField of the scale factor with scale factor ID scalID. All scale
    factor information are extracted from cfg_lines.
    
    Parameters
    ----------
    cfg_lines : [character]
        List of configuration file lines
    scalID: [integer]
        scale factor ID of interest

    Returns
    ----------
    scalfld : :class:`GCField` object.

    History
    ----------
    20140217 ckeller: Initial version    
    """   
    
    scalfld = None
     
    # identify start of settings section
    eof = len(cfg_lines)-1
    idx = find_substr_index( cfg_lines, start)
    
    # read settings and add to emis_setup until end of settings reached. 
    idx = idx+1
    while True:
        
        # exit loop?
        if idx > eof:
            break
        if end in cfg_lines[idx]:
            break        
        
        # split line
        if isMask:
            expLen=9
        else:
            expLen=8
        spl = config_line_split( cfg_lines[idx], expLen=expLen )
        
        # empty list = this line is a comment
        if len(spl) == 0:
            idx=idx+1
            continue
 
        # get scale factor ID
        thisID = int(spl[0])
 
        # skip if this scale factor ID is not used
        if scalID != thisID:
            idx=idx+1
            continue
 
        # extract values
        fldname = spl[1]
        srcfile = str(spl[2])
        srcvar  = str(spl[3])
        srctime = str(spl[4])
        srcdim  = str(spl[5])
        srcunit = str(spl[6])
        oper    = str(spl[7])
         
        # mask fields must have 4 scale factors = mask regions
        if isMask:
            mask_window = [float(x) for x in spl[8].split('/')]
            scalfactors = []
            if len(mask_window) != 4:
                msg = 'Illegal mask field windows: '+fldname+' ('+str(mask_window)+')'
                raise ValueError(msg)
                    
        # eventually extract scale factors from file
        if srcvar == "-":
            scalfactors = [float(x) for x in srcfile.split('/')]
            srcfile = '-'
        else:
            scalfactors = []
        
        # default srctime:
        if srctime == "-":
            srctime = "*/*/*/*"
        
        # add field information, incl. metadata
        scalfld = pyhemco.emissions.GCField(fldname,
                                            filename=srcfile,
                                            var_name=srcvar,
                                            unit=srcunit,
                                            ndim=srcdim,
                                            data=scalfactors )
        
        if isMask:
            pyhemco.emissions.mask(scalfld, scalfld.name, srctime, mask_window=mask_window, fid=thisID)
        else:
            pyhemco.emissions.scale_factor(scalfld, scalfld.name, srctime, operator=oper, fid=thisID)
        
        # stop here if scalID is defined
        break
    
    return scalfld


def read_extensions( emis_setup, cfg_lines, start="BEGIN SECTION EXTENSION SWITCHES", 
                     end="END SECTION EXTENSION SWITCHES", read_all=False ):
    """
    Extracts the HEMCO extension switches from cfg_lines and registers the base 
    emission fields of all enabled extensions.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be created & filled).
    cfg_lines : [character]
        List of configuration file lines.
    start : [character]
        Start scanning file from this line
    end : [character]
        Scan file up to this line
    read_all : [boolean]
        If True, reads all extensions data. Otherwise, reads only enabled extensions.

    History
    ----------
    20140217 ckeller: Initial version
    """   
    # identify start of settings section 
    idx = find_substr_index( cfg_lines, start)
    eof = len(cfg_lines)-1
    
    # read settings and add to emis_setup until end of settings reached. 
    idx = idx+1
    while True:
        
        # exit loop?
        if idx > eof:
            break
        if end in cfg_lines[idx]:
            break        
        
        # split line
        spl = config_line_split( cfg_lines[idx], expLen=4 )
        
        # empty list = this line is a comment
        if len(spl) == 0:
            idx=idx+1
            continue
        
        # extract values
        ExtNr   = int(spl[0])
        ExtName = str(spl[1])
        onoff   = str(spl[2])
        species = spl[3].split('/')
            
        if onoff.lower()=='on':
            ExtUse=True
        else:
            ExtUse=False
                
        thisext = pyhemco.emissions.EmissionExt(ExtName, enabled=ExtUse, eid=ExtNr, species=species)
                
        # now read all base emissions belonging to this extension
        if read_all or ExtUse:
            read_base_emissions( emis_setup, cfg_lines, start="BEGIN SECTION EXTENSION DATA", 
                                 end="END SECTION EXTENSION DATA", extension=thisext, read_all=read_all )
        # increase line index
        idx = idx+1

def add_header( outfile, section ):
    outfile.write('\n')
    outfile.write(SEPARATOR+'\n')
    outfile.write('BEGIN SECTION '+section+'\n')
    outfile.write(SEPARATOR+'\n')
 
def add_footer( outfile, section ):
    outfile.write('\n')
    outfile.write('END SECTION '+section+'\n') 

def field2file( field, outfile, emis_setup, style ):
    """
    Writes a GCField object (field) to a configuration file.
    
    Parameters
    ----------
    field : :class:`GCField` object.
        field that shall be written to file.
    outfile :
        Already opened file to write into.
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be written into file).
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    # base field or scale field?
    if pyhemco.emissions.BEF_ATTR_NAME in field.attributes.keys():
        isBase = True
        attrs  = field.attributes[pyhemco.emissions.BEF_ATTR_NAME]
    else:
        isBase = False
        attrs  = field.attributes[pyhemco.emissions.SF_ATTR_NAME]
    
    # extract information to be written into file
               
    # field name
    fldname = str(field.name)    
    
    # source file information
    srcfile   = str(field.filename)
    srcvar    = str(field.var_name)
    srcunit   = str(field.unit)
    srctime   = str(attrs['timestamp'])
    
    # eventually write data directly into file:
    if srcfile == '-':
        srcfile = '/'.join([str(i) for i in list(field.data) ] )
        srctime = '-'
        srcvar  = '-'
        
    # data dimension
    if field.ndim==2:
        srcdim='xy'
    elif field.ndim==3:
        srcdim='xyz'
    else:
        raise ValueError('Illegal source dimension in '+fldname)
    
    # BASE FIELDS
    if isBase:
        if attrs['extension'] is None:
            fid = '0'
        else:
            fid = str(attrs['extension'].eid)
            
        spec = str(attrs['species'])
        cat  = str(attrs['category'])
        hier = str(attrs['hierarchy'])
        
        scalIDs = [ str(scal.attributes[pyhemco.emissions.SF_ATTR_NAME]['fid']) for scal in attrs['scale_factors'] ]
        if len(scalIDs)>0:
            scalIDs = '/'.join(scalIDs)
        else:
            scalIDs = '-'
                
        fldstr = ' '.join([fid, fldname, srcfile, srcvar, srctime, srcdim, srcunit, spec, scalIDs, cat, hier])
        
    # SCALE FACTORS / MASKS 
    else:        
        fid  = str(attrs['fid'])
        oper = str(attrs['operator'])
        if 'mul' in oper:
            oper = '1'
        elif 'div' in oper:
            oper = '-1'
        elif 'sqr' in oper:
            oper = '2'               
        fldstr = ' '.join([fid, fldname, srcfile, srcvar, srctime, srcdim, srcunit, oper])
             
        # for masks:
        if 'mask_window' in attrs.keys():
            data = '/'.join(str(i) for i in attrs['mask_window'])
            fldstr = ' '.join([fldstr, data])
                                
    # write to file
    outfile.write(fldstr+'\n')
        
            
def write_settings( emis_setup, outfile, style ):
    """
    Write emission setup into a configuration file.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (to be written into file).
    outfile :
        Already opened file to write into.
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    add_header( outfile, 'SETTINGS')
    
    for k, v in emis_setup.extra_settings.items():
        outfile.write(str(k)+': '+str(v)+'\n')
        
    add_footer( outfile, 'SETTINGS')  

def write_base_emissions( emis_setup, outfile, style ):
    """
    Write base emission information into a configuration file.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (from which information is taken from).
    outfile :
        Already opened file to write into.
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    add_header( outfile, 'BASE EMISSIONS')
    outfile.write('# ExtNr Name sourceFile sourceVar sourceTime SrcDim SrcUnit Species ScalIDs Cat Hier\n')
    
    for iField in emis_setup.base_emission_fields:
        if not iField.is_extbase():
            field2file( iField, outfile, emis_setup, style )
        
    add_footer( outfile, 'BASE EMISSIONS')  


def write_scale_factors( emis_setup, outfile, style ):
    """
    Write scale factor information into a configuration file.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (from which information is taken from).
    outfile :
        Already opened file to write into.
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    add_header( outfile, 'SCALE FACTORS')
    outfile.write('# ScalID Name sourceFile sourceVar sourceTime SrcDim SrcUnit Oper Scalar\n')
    
    for iField in emis_setup.scale_factors:
        if not iField.is_mask():
            field2file( iField, outfile, emis_setup, style )
        
    add_footer( outfile, 'SCALE FACTORS')  


def write_masks( emis_setup, outfile, style ):
    """
    Write mask information into a configuration file.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (from which information is taken from).
    outfile :
        Already opened file to write into.
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    add_header( outfile, 'MASKS')
    outfile.write('# ScalID Name sourceFile sourceVar sourceTime SrcDim SrcUnit Oper Lon1/Lat1/Lon2/Lat2\n')
    
    for iField in emis_setup.scale_factors:
        if iField.is_mask():
            field2file( iField, outfile, emis_setup, style )
        
    add_footer( outfile, 'MASKS')  


def write_extensions( emis_setup, outfile, style ):
    """
    Writes extension information into a configuration file.
    
    Parameters
    ----------
    emis_setup : :class:`Emissions` object.
        The emissions setup object (from which information is taken from).
    outfile :
        Already opened file to write into.
    style : (string)
        file type. 'HEMCO' for a HEMCO-style file, 'ESMF' for 
        an ESMF-style file.

    History
    ----------
    20140224 ckeller: Initial version    
    """
    
    # Extension switches
    add_header( outfile, 'EXTENSION SWITCHES')
    outfile.write('# ExtNr ExtName     on/off Species\n')
    for iExt in emis_setup.extensions:
        if iExt.enabled:
            onoff='on'
        else:
            onoff='off'
        species = '/'.join(iExt.species)
        fldstr = ' '.join([str(iExt.eid), str(iExt.name), onoff, species])
        outfile.write(fldstr+'\n')
    add_footer( outfile, 'EXTENSION SWITCHES')  

    # Extension data
    add_header( outfile, 'EXTENSION DATA')
    outfile.write('# ExtNr Name sourceFile sourceVar sourceTime SrcDim SrcUnit Species ScalIDs Cat Hier\n')
    for iField in emis_setup.base_emission_fields:
        if iField.is_extbase():
            field2file( iField, outfile, emis_setup, style )       
    add_footer( outfile, 'EXTENSION DATA')      
      
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
