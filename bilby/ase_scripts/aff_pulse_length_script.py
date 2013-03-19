# File name: aff_pulsed_gate_script.py
# Designed for STM fabricated devices - very slow ramping and hold at final voltages
#
# This example should be run with "execfile('aff_pulsed_gate_script.py')"
#
# Updated by: Sam Hile <samhile@gmail.com>, 2011

from numpy import pi, random, arange, size
from time import time,sleep

# Create instruments
ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1')
HPPulse = qt.instruments.create('HPPulse','HP_8131A',id='GPIB::21')

# Set current gain mV/nA
V_gain = 10000.0        ##CHECK Match Amplifier Gain

# Set ramping speed limits for dac initial and rewind
# stepsize in mV
RampStep = 5
# wait time in seconds
RampWait = 0.05

# Set pulse generator
HPPulse.set_period(1e-6)        ##CHECK T_p
HPPulse.set_width(1e-8)        ##CHECK T_h
HPPulse.set_low(0)        ##CHECK HPV_l
HPPulse.set_high(3)        ##CHECK HPV_h

# create dacs list, first two will be swept 
v_dac = []
v_vec = []

# select dac number: ('dac4')/('dac11')
# select start, end, and increment values: arange(start,end,increment))
v_dac.append('dac4')        ##CHECK V_pulse
v_vec.append(arange(0,500,1))        ##CHECK

v_dac.append('dac1')        ##CHECK V_gate
v_vec.append(arange(-50,50,0.1))        ##CHECK

# From here on it will be static dacs (add or remove as needed)
v_dac.append('dac8')        ##CHECK V_sd
v_vec.append([0])        ##CHECK

v_dac.append('dac3')        ##CHECK V_pulsebase
v_vec.append([0])        ##CHECK

# create vectors to ramp from current value to initial value, and rewind the inner loop
# set speed with 3rd arg of arange() - step size; and msleep() time below
v_start_ramp = []
v_rewind_ramp = []
for idx,v in enumerate(v_vec):
    #get current value from instrument
    currV = ivvi.get(v_dac[idx])
    print 'about to ramp from %f mV to start level' % currV
    v_start_ramp.append(arange(currV,v[0],RampStep))
    v_rewind_ramp.append(arange(v[-1],v[0],RampStep))

# you indicate that a measurement is about to start and other
# processes should stop (like batterycheckers, or temperature
# monitors)
qt.mstart()

# Turn pulses on
HPPulse.on()

# Ramp all dacs to initial value
for idx,dac in enumerate(v_dac):
    for v in v_start_ramp[idx]:
        ivvi.set(dac,v)
        qt.msleep(RampWait)

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='aff_pulse_map')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('V_pulse [mV]')
data.add_coordinate('V1_gate [mV]')
data.add_value('I_sd [nA]')

# The next command will actually create the dirs and files, based
# on the information provided above. Additionally a settingsfile
# is created containing the current settings of all the instruments.
data.create_file()

# Next two plot-objects are created. First argument is the data object
# that needs to be plotted. To prevent new windows from popping up each
# measurement a 'name' can be provided so that window can be reused.
# If the 'name' doesn't already exists, a new window with that name
# will be created. For 3d plots, a plotting style is set.
# Comment out if unwanted
plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2)
plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')
                                    ##CHECK 2d/3d mode

print 'measurement starting'
# preparation is done, now start the measurement.
# It is actually a simple loop.
FirstSweep = True
for v1 in v_vec[0]:
    # set V_pulse
    ivvi.set(v_dac[0],v1)

    #rewind if not first iteration
    if not FirstSweep:
        for v in v_start_ramp[idx]:
            ivvi.set(dac,v)
            qt.msleep(RampWait)
    FirstSweep = False
    
    qt.msleep(0.1)          ##CHECK Wait before sweep
    for v2 in v_vec[1]:
        # set V_gate
        ivvi.set(v_dac[1],v2)

        # wait for amplifier to settle???
        qt.msleep(0.005)          ##CHECK Wait before measure

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

#leave dacs hanging

#Turn pulses off
HPPulse.off()
        
# lastly tell the secondary processes (if any) that they are allowed to start again.
qt.mend()
