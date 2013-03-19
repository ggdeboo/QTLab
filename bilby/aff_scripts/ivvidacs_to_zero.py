ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
for idx in arange(1,17):
    print 'Ramping dac%s...' %idx
    ivvi.set('dac%s' %idx,0)
    qt.msleep(0.001)