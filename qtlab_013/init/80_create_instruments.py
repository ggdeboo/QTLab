##########G02 VTI RACK######
#LockIn1 = qt.instruments.create('LockIn1', 'x_SR830', address='GPIB::5', reset=False)
#LockIn2 = qt.instruments.create('LockIn2', 'x_SR830', address='GPIB::4', reset=False)
#Magnet1 = qt.instruments.create('Magnet1', 'x_AMI_420', address='GPIB::22', reset=False)
#TempCon1 = qt.instruments.create('TempCon1', 'x_Cryocon_32B', address='GPIB::12', reset=False)
#Source1 = qt.instruments.create('Source1', 'x_Yokogawa_7651', address='GPIB::4', reset=False)
#Meter1 = qt.instruments.create('Meter1', 'x_Keithley_2001', address='GPIB::16', reset=False)

##########Examples##########
#example1 = qt.instruments.create('example1', 'example', address='GPIB::1', reset=True)
#dsgen = qt.instruments.create('dsgen', 'dummy_signal_generator')
#pos = qt.instruments.create('pos', 'dummy_positioner')
#combined = qt.instruments.create('combined', 'virtual_composite')
#combined.add_variable_scaled('magnet', example1, 'chA_output', 0.02, -0.13, units='mT')
#combined.add_variable_combined('waveoffset', [{
#    'instrument': dmm1,
#    'parameter': 'ch2_output',
#    'scale': 1,
#    'offset': 0}, {
#    'instrument': dsgen,
#    'parameter': 'wave',
#    'scale': 0.5,
#    'offset': 0
#    }], format='%.04f')
