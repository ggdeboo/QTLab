# VTI Hall bar measurement
# Sam Hile  <samhile@gmail.com> 2013

# imports
from numpy import pi, random, arange, size

# Create instruments -assume is done
# LockIn1 = qt.instruments.create('LockIn1', 'x_SR830', address='GPIB::5', reset=False)
# LockIn2 = qt.instruments.create('LockIn2', 'x_SR830', address='GPIB::4', reset=False)
# Magnet1 = qt.instruments.create('Magnet1', 'x_AMI_420', address='GPIB::22', reset=False)
# TempCon1 = qt.instruments.create('TempCon1', 'x_Cryocon_32B', address='GPIB::12', reset=False)

# Define static parameters
v_drive = 0.3 #V
#r_drive = 2e6 #Ohm
#i_drive = 147e-9 #A
f_drive = 17 #Hz

# Define paremeter vectors
# enter start, end, and increment values: arange(start,end,increment))
B_field = arange(0,1.0001,0.005)

# Setup to begin
LockIn1.set_amplitude(v_drive)
LockIn1.set_frequency(f_drive)
Magnet1.set_field_setpoint(B_field[0])
Magnet1.ramp()

qt.mstart()
while(Magnet1.get_state()!=2): #2=holding at setpoint
    qt.msleep(1)
qt.mend()

# Make data object
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='vti_run')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('B [T]')
data.add_value('V_xx [V]')
data.add_value('V_xy [V]')
data.add_value('V_xx Q [V]')
data.add_value('V_xy Q [V]')

# The next command will actually create the dirs and files, based
# on the information provided above. Additionally a settingsfile
# is created containing the current settings of all the instruments.
data.create_file()

# Next plot-objects are created. First argument is the data object
# that needs to be plotted. To prevent new windows from popping up each
# measurement a 'name' can be provided so that window can be reused.
# If the 'name' doesn't already exists, a new window with that name
# will be created. For 3d plots, a plotting style is set.

plot_xx = qt.Plot2D(data, name='V_xx', coorddim=0, valdim=1, maxtraces=2)
plot_xy = qt.Plot2D(data, name='V_xy', coorddim=0, valdim=2, maxtraces=1)

# preparation is done, now start the measurement.
print 'measurement started'
qt.mstart()

# It is actually a simple loop.

for B in B_field:
    Magnet1.set_field_setpoint(B)
    # Pause to let the current meter settle
    while(Magnet1.get_state()!=2):
        qt.msleep(0.2)
        
    # readout
    xx = LockIn1.get_X()
    xy = LockIn2.get_X()
    xxq = LockIn1.get_Y()
    xyq = LockIn2.get_Y()
    # save the data point to the file, this will automatically trigger
    # the plot windows to update
    data.add_data_point(B, xx, xy, xxq, xyq)
    # the next function is necessary to keep the gui responsive. It
    # checks for instance if the 'stop' button is pushed. It also checks
    # if the plots need updating.
    plot_xx.update()
    plot_xy.update()

qt.mend()
# after the measurement ends, you need to close the data file.
data.close_file()
plot_xx.save_png()
plot_xy.save_png()


print 'measurement finished'