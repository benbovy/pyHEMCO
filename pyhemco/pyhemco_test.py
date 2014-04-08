# some test code for the pyhemco tools.

# import pyhemco
import sys
sys.path.append('/Users/Christoph/Documents/PROJECTS/HEMCO/prog/PyProg/pyHEMCO')
from pyhemco import emissions


# read/write config file 
infile = '/Users/Christoph/Documents/PROJECTS/HEMCO/prog/PyProg/pyHEMCO/HEMCO_Config'
outfile = '/Users/Christoph/Documents/PROJECTS/HEMCO/prog/PyProg/pyHEMCO/HEMCO_Config.out'

setup1 = emissions.load_emissions_file(infile)
setup1.save(outfile)
setup2 = emissions.load_emissions_file(outfile)


# manually create an emission setup

# create setup first (fill afterwards)
this_setup = emissions.Emissions( [], description='Test setup' )

# create GCField entry
fld_name     = 'GEIA_NO'
fld_var_name = 'NO'
fld_filename = 'geia.nc'
fld_ndim     = 2
fld_unit     = 'kg/m2/s'
newfld = emissions.GCField(fld_name, 
                           var_name=fld_var_name,
                           filename=fld_filename,
                           ndim=fld_ndim,
                           unit=fld_unit)

# add metadata to this field - don't add scale factors yet!
fld_srcdate   = '1985/1-12/1/0'
fld_srcvar    = 'NO'
fld_category  = 1
fld_hierarchy = 1
emissions.base_emission_field(newfld, newfld.name, fld_srcdate, fld_srcvar,
                              fld_category, fld_hierarchy)

# add to the setup
this_setup.base_emission_fields.add(newfld)

# add scale factors
fld_name     = 'NOXScalar'
fld_var_name = 'NOXScalar'
fld_filename = 'NOXScalar.nc'
fld_ndim     = 2
fld_unit     = 'unitless'
newscl = emissions.GCField(fld_name, 
                           var_name=fld_var_name,
                           filename=fld_filename,
                           ndim=fld_ndim,
                           unit=fld_unit)

this_scl = emissions.scale_factor(newscl, 'TOTFUEL_THISYR', '1985-2008/1/1/0', operator='*',
                                  fid=1, copy=True)

basefld = this_setup.base_emission_fields.get_object(name='GEIA_NO')
basefld.emission_scale_factors.add(this_scl)

#
##
### eof ###