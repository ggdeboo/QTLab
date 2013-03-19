import gtk
import gtk.glade
import gobject
import qt
from clean_stabgui import Stabgui

def initialize_gui(xml):  # Create ListStores
    dacstore1 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac1').set_model(dacstore1)
    dacstore2 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac2').set_model(dacstore2)
    dacstore3 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac3').set_model(dacstore3)
    dacstore4 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac4').set_model(dacstore4)
    dacstore5 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac5').set_model(dacstore5)
    dacstore6 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac6').set_model(dacstore6)
    dacstore7 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac7').set_model(dacstore7)
    dacstore8 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac8').set_model(dacstore8)
    dacstore9 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac9').set_model(dacstore9)
    dacstore10 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac10').set_model(dacstore10)
    dacstore11 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac11').set_model(dacstore11)
    dacstore12 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac12').set_model(dacstore12)
    dacstore13 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac13').set_model(dacstore13)
    dacstore14 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac14').set_model(dacstore14)
    dacstore15 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac15').set_model(dacstore15)
    dacstore16 = gtk.ListStore(gobject.TYPE_STRING)
    xml.get_widget('outputdac16').set_model(dacstore16)

    for idx in range(16):
      	xml.get_widget('outputdac%d' %(idx+1)).append_text('none')
       	for jdx in range (16):
       		xml.get_widget('outputdac%d' %(idx+1)).append_text('dac%d' %(jdx+1))
       	xml.get_widget('outputdac%d' % (idx+1)).set_text_column(0)	
       	xml.get_widget('outputdac%d' % (idx+1)).set_active(0)

    polstore = gtk.ListStore(gobject.TYPE_STRING)
    polstore.append(['NEG'])
    polstore.append(['BIP'])
    polstore.append(['POS'])
     		
    inputstore = gtk.ListStore(gobject.TYPE_STRING)
    inputstore.append(['none'])
    for idx in range(16):
      	inputstore.append(['ai%d' % (idx)])	
    for idx in range(3):
       	xml.get_widget('input%d' % (idx+1)).set_model(inputstore)
        xml.get_widget('input%d' % (idx+1)).set_text_column(0)
        xml.get_widget('input%d' % (idx+1)).set_active(0)
    for idx in range(4):
      	xml.get_widget('pol%d' % (idx+1)).set_model(polstore)
       	xml.get_widget('pol%d' % (idx+1)).set_text_column(0)
       	xml.get_widget('pol%d' % (idx+1)).set_active(0)

def fill_entries(xml,settings):
    fill_entries1(xml,settings)
    fill_entries2(xml,settings)

def fill_entries1(xml,settings):
    ##------------------------------EXPERIMENT------------------------------##
    # Set instrument checkboxes
    xml.get_widget('checkRF1').set_active(settings['checkRF1'])
    xml.get_widget('checkRF2').set_active(settings['checkRF2'])
    xml.get_widget('checkMW').set_active(settings['checkMW'])		
    xml.get_widget('checkMag').set_active(settings['checkMag'])
    xml.get_widget('checkTemp').set_active(settings['checkTemp'])
    xml.get_widget('checkLaser').set_active(settings['checkLaser'])

def fill_entries2(xml,settings):
    # Set instrument addresses
    for idx,s in enumerate(settings['addr']):
        xml.get_widget('addr%d' % (idx+1)).set_text(s)
    # Set magnet sweep rate
    xml.get_widget('magrate').set_text('%s' % settings['magrate'])
    # Set output polarity values
    for idx,s in enumerate(settings['pol']):
        xml.get_widget('pol%d' % (idx+1)).set_active(s)
    # Set pause times
    xml.get_widget('pause1').set_text('%s' % settings['pause1'])
    xml.get_widget('pause2').set_text('%s' % settings['pause2'])
    # Set filename
    xml.get_widget('filename').set_text(settings['filename'])
        
    ##------------------------------OUTPUT------------------------------##
    # Set output dac values
    for idx,s in enumerate(settings['outputdac']):
        xml.get_widget('outputdac%d' % (idx+1)).set_active(s)
    # Set output label
    for idx,s in enumerate(settings['outputlabel']):
        xml.get_widget('outputlabel%d' % (idx+1)).set_text(s)
    # Set output start values
    for idx,s in enumerate(settings['start']):
        xml.get_widget('start%d' % (idx+1)).set_text('%s' %s)
    # Set dynamic true/false
    for idx,s in enumerate(settings['dynamic']):
        xml.get_widget('dyna%d' % (idx+1)).set_active(s)
    # Set output order values
    for idx,s in enumerate(settings['order']):
        xml.get_widget('order%d' % (idx+1)).set_text('%s' %s)				
    # Set output stop values
    for idx,s in enumerate(settings['stop']):
        xml.get_widget('stop%d' % (idx+1)).set_text('%s' %s)
    # Set output increment values
    for idx,s in enumerate(settings['incr']):
        xml.get_widget('incr%d' % (idx+1)).set_text('%s' %s)

    ##------------------------------INPUT------------------------------##
    # Set input channels
    for idx,s in enumerate(settings['input']):
        xml.get_widget('input%d' % (idx+1)).set_active(s)
    # Set input gain
    for idx,s in enumerate(settings['inputgain']):
        xml.get_widget('inputgain%d' % (idx+1)).set_text('%s' %s)
    # Set input label
    for idx,s in enumerate(settings['inputlabel']):
        xml.get_widget('inputlabel%d' % (idx+1)).set_text(s)
    # Set plot checkboxes
    for idx,s in enumerate(settings['plot2d']):
        xml.get_widget('plot2d%d' % (idx+1)).set_active(s)
    for idx,s in enumerate(settings['plot3d']):
        xml.get_widget('plot3d%d' % (idx+1)).set_active(s)
    # Set normal/log checkboxes
    for idx,s in enumerate(settings['normal']):
        xml.get_widget('normal%d' % (idx+1)).set_active(s)
    for idx,s in enumerate(settings['log']):
        xml.get_widget('log%d' % (idx+1)).set_active(s)
    # Set samplerate
    xml.get_widget('samplerate').set_text('%s' % settings['samplerate'])
    # Set constant/auto and number of samples/precision
    xml.get_widget('constant').set_active(settings['constant'])
    xml.get_widget('auto').set_active(settings['auto'])
    xml.get_widget('num_samples').set_text('%s' % settings['num_samples'])
    xml.get_widget('precision').set_text('%s' % settings['precision'])
            
def get_entries(xml,settings):
    ##------------------------------EXPERIMENT------------------------------##
    # Get instrument checkboxes
    settings['checkRF1'] = xml.get_widget('checkRF1').get_active()
    settings['checkRF2'] = xml.get_widget('checkRF2').get_active()
    settings['checkMag'] = xml.get_widget('checkMag').get_active()
    settings['checkMW'] = xml.get_widget('checkMW').get_active()
    settings['checkTemp'] = xml.get_widget('checkTemp').get_active()
    settings['checkLaser'] = xml.get_widget('checkLaser').get_active()
    # Get instrument addresses
    for idx in range(4):
        settings['addr'].append(xml.get_widget('addr%d' % (idx+1)).get_text())
    # Get magnet sweep rate
    settings['magrate'] = xml.get_widget('magrate').get_text()
    # Get output polarity values 
    for idx in range(4):
        settings['pol'].append(xml.get_widget('pol%d' % (idx+1)).get_active())
    # Get pause times
    settings['pause1'] = xml.get_widget('pause1').get_text()
    settings['pause2'] = xml.get_widget('pause2').get_text()
    # Get filename
    settings['filename'] = xml.get_widget('filename').get_text()
    ##------------------------------OUTPUT------------------------------##
    # Get output variables
    for idx in range(16):
        settings['outputdac'].append(xml.get_widget('outputdac%d' % (idx+1)).get_active())
        settings['start'].append(xml.get_widget('start%d' % (idx+1)).get_text())
        settings['outputlabel'].append(xml.get_widget('outputlabel%d' % (idx+1)).get_text())
        settings['dynamic'].append(xml.get_widget('dyna%d' % (idx+1)).get_active())
        settings['order'].append(xml.get_widget('order%d' % (idx+1)).get_text())
        settings['stop'].append(xml.get_widget('stop%d' % (idx+1)).get_text())
        settings['incr'].append(xml.get_widget('incr%d' % (idx+1)).get_text())
        if xml.get_widget('outputdac%d' % (idx+1)).get_active() != 0:
            settings['number_of_outputs']=settings['number_of_outputs']+1
            if xml.get_widget('dyna%d' % (idx+1)).get_active() != 0:
                settings['number_of_sweeps']=settings['number_of_sweeps']+1
    ##------------------------------INPUT------------------------------##
    # Get input variables
    for idx in range(3):
        settings['input'].append(xml.get_widget('input%d' % (idx+1)).get_active())	
        settings['inputgain'].append(xml.get_widget('inputgain%d' % (idx+1)).get_text())
        settings['inputlabel'].append(xml.get_widget('inputlabel%d' % (idx+1)).get_text())
        settings['plot2d'].append(xml.get_widget('plot2d%d' % (idx+1)).get_active())
        settings['plot3d'].append(xml.get_widget('plot3d%d' % (idx+1)).get_active())
        settings['normal'].append(xml.get_widget('normal%d' %(idx+1)).get_active())
        settings['log'].append(xml.get_widget('log%d' %(idx+1)).get_active())
        if xml.get_widget('input%d' % (idx+1)).get_active() != 0:
            settings['number_of_measurements']=settings['number_of_measurements']+1
    # Get samplerate                                                   				
    settings['samplerate'] = xml.get_widget('samplerate').get_text()
    # Set constant/auto and number of samples/precision
    settings['constant'] = xml.get_widget('constant').get_active()
    settings['auto'] = xml.get_widget('auto').get_active()
    settings['num_samples'] = xml.get_widget('num_samples').get_text()
    settings['precision'] = xml.get_widget('precision').get_text()
