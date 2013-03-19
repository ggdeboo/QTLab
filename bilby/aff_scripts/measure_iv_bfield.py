# File name: measure_iv_bfield.py
#
# This script should be run with "execfile('measure_iv_bfield.py')"

from numpy import pi, random, arange, size
from time import time,sleep


# Set magnetic field
def set_field(value):
    if not magnet.get_activity()==0:
        magnet.hold()
    if not magnet.get_switch_heater()==1:
        magnet.heater_on()

    magnet.set_field_setpoint('%2.2f' % value)
    magnet.to_setpoint()
    print 'Sweeping magnetic field to %2.2f Tesla...' % value
    while abs(magnet.get_field()-value) > 0.0001:
        sleep(1)

    magnet.hold()
    print 'Desired field reached.'
    print ''

# Set magnetic field to zero
def ramp_field_to_zero():
    if not magnet.get_activity()==0:
        magnet.hold()
    if not magnet.get_switch_heater()==1:
        magnet.heater_on()

    magnet.to_zero()
    print 'Sweeping magnetic field to zero...'
    while magnet.get_field() > 0.0001:
        sleep(1)

    magnet.hold()    
    print 'Field at zero.'

# Initialize magnet
def init_magnet(sweeprate):
    magnet.get_all()
    magnet.remote()
    magnet.hold()
    magnet.set_sweeprate_field('%2.2f' % sweeprate)
    if not magnet.get_activity()==0:
        magnet.hold()

number_of_samples=10000
samplerate=1e5

# Create instruments
ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1',
                               samples=number_of_samples,freq=samplerate)
magnet = qt.instruments.create('IPS120','OxfordInstruments_IPS120',address='COM3')

# Set I gain MV/A
I_gain = 1000

# create dacs, first will be swept
v_dac = []
v_vec = []

v_dac.append('dac2')
v_vec.append(arange(30,180.01,0.1))

# From here on it will be static dacs
v_dac.append('dac1')
v_vec.append([-0.35]) # -0.45 results in 0.1 mV on sample

# Create ramp vector for the magnetic field
b_vec=arange(10,-0.1,-0.1)

# Plots to update
p2D=False
p3D=True

# you indicate that a measurement is about to start and other
# processes should stop (like batterycheckers, or temperature
# monitors)
qt.mstart()

# Ramp dacs to initial value
for idx,dac in enumerate(v_dac):
    ivvi.set(dac,v_vec[idx][0])
    sleep(0.001)

# Initialize magnet and set sweep rate
init_magnet(0.8)

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='QK22WIRON3D4_IVg_vs_B_Vb210uV_285mK')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('V [mV]')
data.add_coordinate('B [T]')
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
if p2D:
    plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, maxtraces=1)
if p3D:
    plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

# preparation is done, now start the measurement.
# It is actually a simple loop.
print 'Measurement started...'
print ''
for b in b_vec:
    # set the magnetic field
    set_field(b)
    print 'Wait 20 seconds to get back to base temperature...'
    print ''
    sleep(20)
    print 'Recording data...'
    print ''
    for v in v_vec[0]:
        # set the voltage
        ivvi.set(v_dac[0],v)
        sleep(0.020)

        # readout
        result = NIDev1.get('ai0')*1000/I_gain

        # save the data point to the file, this will automatically trigger
        # the plot windows to update
        data.add_data_point(v, b, result)

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

# Sweep magnet to zero switch back to local control
ramp_field_to_zero()
magnet.heater_off()
magnet.local()

# Save plots to figures
if p2D:
    plot2d.save_png()
if p3D:
    plot3d.save_png()    

#ramp dacs back to zero
for idx,dac in enumerate(v_dac):
   	ivvi.set(dac,0)
   	qt.msleep(0.001)
print 'Measurement finished.'

# lastly tell the secondary processes (if any) that they are allowed to start again.
qt.mend()