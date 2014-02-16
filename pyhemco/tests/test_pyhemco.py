
import sys

sys.path.append('/Users/Christoph/Documents/PROJECTS/HEMCO/prog/PyProg/pyHEMCO/pyhemco/')
from emissions import Emissions
from emissions import GCField
from emissions import EmissionExt
from emissions import base_emission_field
from emissions import load_emissions_file

# create a dummy field
testField = GCField('test_emissions',standard_name='test_emissions',unit='kg/m2/s',filename='test.nc')

basefield1 = base_emission_field(testField, 1, 'test_base1', '2009/01/01/01', 'NO', 1, 1)





#
#
## eof ###