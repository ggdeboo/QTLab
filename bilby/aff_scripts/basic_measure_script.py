# File name: basic_measure_script.py
#
# This example should be run with "execfile('basic_measure_script.py')"

from numpy import pi, random, arange, size
from time import time,sleep

# Create instruments
ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1')

# Set I gain mV/nA
V_gain = 1.0

# create dacs, first two will be swepped 
v_dac = []
v_vec = []

v_dac.append('dac1')
v_vec.append(arange(0,500,1))

v_dac.append('dac2')
v_vec.append(arange(-50,50,0.1))

# From here on it will be static dacs
v_dac.append('dac8')
v_vec.append([500])

# create vectors to ramp to initial value and back to zero
v_start_ramp = []
v_stop_ramp = []
for v in v_vec:
    v_start_ramp.append(arange(0,v[0],5))
    v_stop_ramp.append(arange(v[-1],0,5))

# you indicate that a measurement is about to start and other
# processes should stop (like batterycheckers, or temperature
# monitors)
qt.mstart()

# Ramp dacs to initial value
for idx,dac in enumerate(v_dac):
    for v in v_start_ramp[idx]:
        ivvi.set(dac,v)
        qt.msleep(0.001)

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='testmeasurement')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('V2 [mV]')
data.add_coordinate('V1 [mV]')
data.add_value('V [mV]')

# The next command will actually create the dirs and files, based
# on the information provided above. Additionally a settingsfile
# is created containing the current settings of all the instruments.
data.create_file()

# Next two plot-objects are created. First argument is the data object
# that needs to be plotted. To prevent new windows from popping up each
# measurement a 'name' can be provided so that window can be reused.
# If the 'name' doesn't already exists, a new window with that name
# will be created. For 3d plots, a plotting style is set.
plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2)
plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

# preparation is done, now start the measurement.
# It is actually a simple loop.
for v1 in v_vec[0]:
    # set the magnetic field
    ivvi.set(v_dac[0],v1)
    for v2 in v_vec[1]:
        # set the frequency
        ivvi.set(v_dac[1],v2)

        # readout
        result = NIDev1.get('ai0')*V_gain

        # save the data point to the file, this will automatically trigger
        # the plot windows to update
        data.add_data_point(v2, v1, result)

        # the next function is necessary to keep the gui responsive. It
        # checks for instance if the 'stop' button is pushed. It also checks
        # if the plots need updating.
        qt.msleep(0.001)

    # the next line defines the end of a single 'block', which is when sweeping
    # the most inner loop finishes. An empty line is put in the datafile, and
    # the 3d plot is updated.
    data.new_block()

# after the measurement ends, you need to close the data file.
data.close_file()

#ramp dacs back to zero
for idx,dac in enumerate(v_dac):
    for v in v_stop_ramp[idx]:
        ivvi.set(dac,v)
        
# lastly tell the secondary processes (if any) that they are allowed to start again.
qt.mend()
