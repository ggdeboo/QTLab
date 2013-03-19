import qt

def checkinstruments(settings)
    if settings['checkRF1']:
        try:
            print clean_stabgui.HPPulse1.get_all()
        except:
            print 'Pulser 1 not set up yet...'
            clean_stabgui.HPPulse1 = qt.instruments.create('HPPulse1','HP_8131A',address=settings['addr1'],reset=False)
        print 'Pulser 1 OK'

    if settings['checkRF2']:
        try:
            print clean_stabgui.HPPulse2.get_all()
        except:
            print 'Pulser 2 not set up yet...'
            clean_stabgui.HPPulse2 = qt.instruments.create('HPPulse2','HP_8131A',address=settings['addr2'],reset=False)
        print 'Pulser 2 OK'

    if settings['checkMW']:
        try:
            print clean_stabgui.MWgen.get_all()
        except:
            print 'MW generator not set up yet...'
            clean_stabgui.MWgen = qt.instruments.create('MWgen','Agilent_E8257C',address=settings['addr3'],reset=False)
        print 'MW generator OK'
        
    if settings['checkMag']:
        try:
            print clean_stabgui.OXMag.get_all()
        except:
            print 'Magnet not set up yet...'
            clean_stabgui.OXMag = qt.instruments.create('OXMag','OxfordInstruments_IPS120',address=settings['addr4'])
        print 'Magnet OK'

    if settings['checkTemp']:
        ##try:
            ##print clean_stabgui.OXtemp.get_all()
        ##except:
            ##print 'Instrument not set up yet...'
            ##clean_stabgui.OXtemp = qt.instruments.create('?','?',address=settings['addr5'])
        print 'Temperature controller cannot be used at the moment'

    if settings['checkLaser']:
        try:
            print clean_stabgui.jdsu.get_all()
        except:
            print 'Laser not set up yet...'
            clean_stabgui.jdsu = qt.instruments.create('jdsu','JDSU_SWS15101',address=settings['addr6'])
        print 'Laser OK'
