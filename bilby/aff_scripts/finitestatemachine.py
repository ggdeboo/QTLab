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

# Create ramps for the gate voltage to the four points
v_00g = arange(188.0,190.01,0.05)
v_00g = scipy.append(v_00g,arange(190.0,187.99,-0.05))
v_01g = arange(188.0,190.01,0.05)
v_01g = scipy.append(v_01g,arange(190.0,187.99,-0.05))
v_10g = arange(188.0,185.99,-0.05)
v_10g = scipy.append(v_10g,arange(186.0,188.01,0.05))
v_11g = arange(188.0,185.99,-0.05)
v_11g = scipy.append(v_11g,arange(186.0,188.01,0.05))
v_dac2 = [v_00g,v_01g,v_10g,v_11g]

# Create ramps for the bias voltage to the four points
v_00b = arange(-41.0,-42.51,-0.0375)
v_00b = scipy.append(v_00b,arange(-42.5,-40.99,0.0375))
v_01b = arange(-41.0,-39.49,0.0375)
v_01b = scipy.append(v_01b,arange(-39.5,-41.01,-0.0375))
v_10b = arange(-41.0,-42.51,-0.0375)
v_10b = scipy.append(v_10b,arange(-42.5,-40.99,0.0375))
v_11b = arange(-41.0,-39.49,0.0375)
v_11b = scipy.append(v_11b,arange(-39.5,-41.01,-0.0375))
v_dac1 = [v_00b,v_01b,v_10b,v_11b]

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='finitestatemachine_results_smooth2')

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
for sum1 in range(4):
	for sum2 in range(4):
		for idx in range(82):
			ivvi.set('dac1',v_dac1[0][idx])
			ivvi.set('dac2',v_dac2[0][idx])
		result = NIDev1.get('ai0')*(1000/I_gain)
		data.add_data_point(188.0, -41.0, result)
		plot2d.update()
		for idx in range(82):
			ivvi.set('dac1',v_dac1[sum1][idx])
			ivvi.set('dac2',v_dac2[sum1][idx])
			result = NIDev1.get('ai0')*(1000/I_gain)
			data.add_data_point(v_dac2[sum1][idx], v_dac1[sum1][idx], result)
			plot2d.update()
		for idx in range(82):
			ivvi.set('dac1',v_dac1[sum2][idx])
			ivvi.set('dac2',v_dac2[sum2][idx])
			result = NIDev1.get('ai0')*(1000/I_gain)
			data.add_data_point(v_dac2[sum2][idx], v_dac1[sum2][idx], result)
			plot2d.update()
		ivvi.set('dac1',-41)
		ivvi.set('dac2',188)
		result = NIDev1.get('ai0')*(1000/I_gain)
		data.add_data_point(188.0, -41.0, result)
		plot2d.update()
		data.new_block()

# after the measurement ends, you need to close the data file.
data.close_file()

#ramp dacs back to zero
ivvi.set('dac1',0)
ivvi.set('dac2',0)
print 'measurement finished'
#-------------------------------------------------------------------------------------------------