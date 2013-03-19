import qt
import time

def createinstruments(settings):

    global ivvi
    global NIDev1
    global HPPulse1
    global HPPulse2
    global MWgen
    global OXMag
    global jdsu
        
    print 'loading instruments...'
    try:
        print ivvi.get_all()
    except:
        ivvi = qt.instruments.create('ivvi','IVVI',address='COM1')
    print 'dacs OK'
    try:
        print NIDev1.get_all()
    except:
        NIDev1 = qt.instruments.create('NIDev1','NI_DAQ',id='Dev1')
    NIDev1.set_samples(settings['num_samples'])
    NIDev1.set_freq(settings['samplerate'])
    print 'adcs OK'
    
    if settings['checkRF1']:
        try:
            print HPPulse1.get_all()
        except:
            print 'Pulser 1 not set up yet...'
            HPPulse1 = qt.instruments.create('HPPulse1','HP_8131A',address=settings['addr'][0],reset=False)
        print 'Pulser 1 OK'

    if settings['checkRF2']:
        try:
            print HPPulse2.get_all()
        except:
            print 'Pulser 2 not set up yet...'
            HPPulse2 = qt.instruments.create('HPPulse2','HP_8131A',address=settings['addr'][1],reset=False)
        print 'Pulser 2 OK'

    if settings['checkMW']:
        try:
            print MWgen.get_all()
        except:
            print 'MW generator not set up yet...'
            MWgen = qt.instruments.create('MWgen','Agilent_E8257C',address=settings['addr'][2],reset=False)
        print 'MW generator OK'
        
    if settings['checkMag']:
        try:
            print OXMag.get_all()
        except:
            print 'Magnet not set up yet...'
            OXMag = qt.instruments.create('OXMag','OxfordInstruments_IPS120',address=settings['addr'][3])
        print 'Magnet OK'

    if settings['checkTemp']:
        ##try:
            ##print OXtemp.get_all()
        ##except:
            ##print 'Instrument not set up yet...'
            ##global OXtemp
            ##OXtemp = qt.instruments.create('?','?',address=settings['addr'][4])
        print 'Temperature controller cannot be used at the moment'

    if settings['checkLaser']:
        try:
            print jdsu.get_all()
        except:
            print 'Laser not set up yet...'
            jdsu = qt.instruments.create('jdsu','JDSU_SWS15101',address=settings['addr'][5])
        print 'Laser OK'

def initinstruments(settings,v_dac,v_vec,instrument_array):
    if settings['checkMag']:
        OXMag.init_magnet(min(self.settings['magrate'],1))	#specify sweeprate in T/min	hardlimit of 1T/min

    print 'setting initial dac values'
        
    for idx in range(16):
        execute_set(settings,v_dac[idx],v_vec[idx][0])

    print 'turning other instruments on if required'

    if settings['checkRF1']:
        HPPulse1.on(1)
        HPPulse1.on(2)
    if settings['checkRF2']:
        HPPulse2.on(1)
    if settings['checkMW']:
        MWgen.on()
    if settings['checkMag']:
        heateroff = True
        for idx in range(settings['number_of_sweeps']):
            if instrument_array[idx] == ('dac%d' % instrumentsused.Magpos):
                heateroff = False
        # Switch heater off if magnet is not swept
        if heateroff:
            if OXMag.get_switch_heater() == 1:
                OXMag.set_switch_heater(0)
##	if self.checkTemp:	
    if settings['checkLaser']:
        jdsu.set('status','ENABLE')
        
def rampback(settings):
    if settings['checkMW']:
        MWgen.off()
        print 'MW generator turned off'
        time.sleep(0.1)
    if settings['checkRF1']:
        pass
        #HPPulse1.off()
    if settings['checkRF2']:
        #HPPulse2.off(1)
        pass
    if settings['checkMag']:
        if OXMag.get_switch_heater() == 1:
            OXMag.set_switch_heater(0)
            print 'magnet heater switched off'
    if settings['checkLaser']:
        jdsu.set('status','DISABLE')
        print 'laser turned off'

def measure_inputs(settings,I_gain):
    global result
    result=[]
    for idx in range (3):
        if settings['input'][idx] != 0:
            if settings['log'][idx] !=0:
                if settings['auto'] !=0:
                    print 'auto'
                    NIDev1.set_samples(10)
                    result_test = (NIDev1.get(settings['input'][idx]))*(1000/I_gain[idx])
                    log_no_of_samples = float(settings['precision'])*4780*exp(-0.0002341*abs(result_test))+6490*exp(-0.009734*abs(result_test))
                    NIDev1.set_samples(log_no_of_samples)																														
                result.append(1/8.488*sinh((NIDev1.get(settings['input'][idx]))*(1000/I_gain[idx])))
            else:
                result.append((NIDev1.get('ai%d' %(settings['input'][idx]-1)))*(1000/I_gain[idx]))
        else:
            result.append(0)

def execute_set(settings,dacnum,value):
    if int(dacnum[3:]) == 0:								# Do nothing if nothing is specified
        pass
    elif int(dacnum[3:]) < 4:    							#it is a voltage DAC 1 to 4
        if settings['pol'][0] == 'NEG':
            ivvi.set(dacnum,value+2000)
        elif settings['pol'][0] == 'POS':
            ivvi.set(dacnum,value-2000)
        else:
            ivvi.set(dacnum,value)
    elif int(dacnum[3:]) < 7:    							#it is a voltage DAC 5 to 7
        if settings['pol'][1] == 'NEG':
            ivvi.set(dacnum,value+2000)
        elif settings['pol'][1] == 'POS':
            ivvi.set(dacnum,value-2000)
        else:
            ivvi.set(dacnum,value)
    elif int(dacnum[3:]) == 8:                              #it is voltage DAC 8
        if settings['pol'][1] == 'NEG':
            ivvi.set(dacnum,value*100+2000)
        elif settings['pol'][1] == 'POS':
            ivvi.set(dacnum,value*100-2000)
        else:
            ivvi.set(dacnum,value*100)
    elif int(dacnum[3:]) < 12:    							#it is a voltage DAC 9 to 12
        if settings['pol'][2] == 'NEG':
            ivvi.set(dacnum,value+2000)
        elif settings['pol'][2] == 'POS':
            ivvi.set(dacnum,value-2000)
        else:
            ivvi.set(dacnum,value)
    elif int(dacnum[3:]) < 15:    							#it is a voltage DAC 13 to 15
        if settings['pol'][3] == 'NEG':
            ivvi.set(dacnum,value+2000)
        elif settings['pol'][3] == 'POS':
            ivvi.set(dacnum,value-2000)
        else:
            ivvi.set(dacnum,value)
    elif int(dacnum[3:]) == 16:    							#it is voltage DAC 16
        if settings['pol'][3] == 'NEG':
            ivvi.set(dacnum,value*100+2000)
        elif settings['pol'][3] == 'POS':
            ivvi.set(dacnum,value*100-2000)
        else:
            ivvi.set(dacnum,value*100)
    elif int(dacnum[3:]) == settings['RF1pos'] and settings['checkRF1']:	    #tRepeat
        HPPulse1.set_period(value)
    elif int(dacnum[3:]) == settings['RF1pos']+1 and settings['checkRF1']:	    #tDelay
        HPPulse1.set_ch1_delay(value)
    elif int(dacnum[3:]) == settings['RF1pos']+2 and settings['checkRF1']:	    #tPulse1
        HPPulse1.set_ch1_width(value)
    elif int(dacnum[3:]) == settings['RF1pos']+3 and settings['checkRF1']:	    #tBlock
        HPPulse1.set_ch2_width(value)
    elif int(dacnum[3:]) == settings['RF2pos'] and settings['checkRF2']:	    #tPulse2
        HPPulse2.set_ch1_width(value)
    elif int(dacnum[3:]) == settings['MWpos'] and settings['checkMW']:		    #MWfreq
        MWgen.set_frequency(value)
    elif int(dacnum[3:]) == settings['MWpos']+1 and settings['checkMW']:	    #MWpow
        MWgen.set_power(value)
    elif int(dacnum[3:]) == settings['Magpos'] and settings['checkMag']:	    #Bfield
        OXMag.ramp_field_to(value)
    elif int(dacnum[3:]) == settings['Temppos'] and settings['checkTemp']:	    #Temperature
        pass
        #OXTemp...(value)
    elif int(dacnum[3:]) == settings['Laserpos'] and settings['checkLaser']:	#Laserwavelength
        jdsu.set('wavelength',value)
    elif int(dacnum[3:]) == settings['Laserpos'] and settings['checkLaser']:	#Laserpower
        jdsu.set('power',value)