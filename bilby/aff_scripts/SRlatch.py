import time
import signal
import scipy
from numpy import pi, random, arange, size
#-------------------------------------------------------------------------------------------------
# Create instruments
ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1',samples=15000,freq=125000)

# Ramp all dacs back to zero
for idx in range(16):
	ivvi.set('dac%d' % (idx+1),0)

# Set I gain mV/nA
I_gain = 100.0

# Create set and reset ramps
v_set = arange(-42,-39.99,0.05)
v_set = scipy.append(v_set,arange(-40,-42.01,-0.05))
v_reset = arange(185.5,187.51,0.05)
v_reset = scipy.append(v_reset,arange(187.5,185.49,-0.05))

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='SRlatch_results_closer')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('V2 [mV]')
data.add_coordinate('V1 [mV]')
data.add_value('I [nA]')

# The next command will actually create the dirs and files, based
# on the information provided above. Additionally a settingsfile
# is created containing the current settings of all the instruments.
data.create_file()

# Next two plot-objects are created. First argument is the data object
# that needs to be plotted. To prevent new windows from popping up each
# measurement a 'name' can be provided so that window can be reused.
# If the 'name' doesn't already exists, a new window with that name
# will be created. For 3d plots, a plotting style is set.
plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, maxpoints=10000, maxtraces=100)

print 'measurement started'				
# preparation is done, now start the measurement.
# It is actually a simple loop.
ivvi.set('dac1',-42.0)
ivvi.set('dac2',185.5)
result = NIDev1.get('ai0')*(1000/I_gain)
data.add_data_point(185.5, -42.0, result)
plot2d.update()
data.new_block()
for v1 in v_set:
	ivvi.set('dac1',v1)
	result = NIDev1.get('ai0')*(1000/I_gain)
	data.add_data_point(185.5, v1, result)
	plot2d.update()
data.new_block()
for v1 in v_set:
	ivvi.set('dac1',v1)
	result = NIDev1.get('ai0')*(1000/I_gain)
	data.add_data_point(185.5, v1, result)
	plot2d.update()
data.new_block()
for v2 in v_reset:
	ivvi.set('dac2',v2)
	result = NIDev1.get('ai0')*(1000/I_gain)
	data.add_data_point(v2, -42.0, result)
	plot2d.update()
data.new_block()
for v2 in v_reset:
	ivvi.set('dac2',v2)
	result = NIDev1.get('ai0')*(1000/I_gain)
	data.add_data_point(v2, -42.0, result)
	plot2d.update()
	
# after the measurement ends, you need to close the data file.
data.close_file()

#ramp dacs back to zero
ivvi.set('dac1',0)
ivvi.set('dac2',0)
print 'measurement finished'
#-------------------------------------------------------------------------------------------------