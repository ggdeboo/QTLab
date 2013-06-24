# June 2013 - Gabriele de Boo
from instrument import Instrument
from lib import visafunc
from time import sleep
import visa
import logging
import types

freqs = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

def int2wvl(i):
    wvl = 900.0+float(i)/4000*200
    return wvl

def wvl2int(wvl):
    i = (wvl-900.0)/200*4000
    return i

class Superlum_BS_1060(Instrument):
    def __init__(self, name, address, reset=False):
        logging.info('Initializing instrument Superlum')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.baud_rate = 57600
        self._visainstrument.term_chars = '\r\n'	

        self._visainstrument.clear()
        self._visainstrument.ask('') # It always returns 'AE' after the clear command

#        self.add_function('reset')
        self.add_function('identify')
        self.add_function('set_to_local')
        self.add_function('set_to_remote')
        self.add_function('set_power_low')
        self.add_function('set_power_high')

        self.add_parameter('Optical_Output',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('Booster_Emission',
            type=types.BooleanType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('power',
            type=types.StringType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('MASTER_KEY_control',
            type=types.BooleanType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('Full_Tuning_Range',
            type=types.ListType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('Operating_Mode',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('Manual_Mode_Wavelength',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('Sweep_Mode_Start',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('Sweep_Mode_End',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('Sweep_Speed',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET, minval=2, maxval=10000, units='nm/s')
        self.add_parameter('Modulation_Mode_Wavelength1',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('Modulation_Mode_Wavelength2',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=1024.0, maxval=1094.0, units='nm')
        self.add_parameter('Modulation_Mode_Frequency',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET, minval=0.1, maxval=1000.0, units='Hz')

        self.get_all()

    def get_all(self):
        self.identify()
        self.get_Optical_Output()
        self.get_Booster_Emission()
        self.get_power()
        self.get_MASTER_KEY_control()
        self.get_Full_Tuning_Range()
        self.get_Operating_Mode()
        self.get_Manual_Mode_Wavelength()
        self.get_Sweep_Mode_Start()
        self.get_Sweep_Mode_End()
        self.get_Sweep_Speed()
        self.get_Modulation_Mode_Wavelength1()
        self.get_Modulation_Mode_Wavelength2()
        self.get_Modulation_Mode_Frequency()
#        self.get_Sweep_Slow()

    def identify(self):
        reply = self._visainstrument.ask('S0')
        if reply.startswith('S20'):
            return reply[3:]

    def do_get_Optical_Output(self):
        reply = self._visainstrument.ask('S20')
        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if ((data1 < 97) or (data1 == 97) or (data1 ==113)):
                return False
            else:
                return True
        elif reply.startswith('AE'):
            print 'Optical Output'
            print 'General error.'
        elif reply.startswith('AL'):
            print 'Instrument is under local control.'

    def do_set_Optical_Output(self, output):
        if output: 
            if not self.do_get_Optical_Output():
                reply = self._visainstrument.ask('S21')
                sleep(0.5)
                self.get_Booster_Emission()
            else:
                print 'Optical output is already enabled.'
        else:
            if self.do_get_Optical_Output():
                reply = self._visainstrument.ask('S21')
                self.get_Booster_Emission()
            else:
                print 'Optical output is already disabled.'

    def do_get_Booster_Emission(self):
        reply = self._visainstrument.ask('S20')
        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if (data2 == 2) or (data2 == 6):
                return False
            else:
                return True
        elif reply.startswith('AE'):
            print 'Booster Emission'
            print 'General error.'
        elif reply.startswith('AL'):
            print 'Instrument is under local control.'

    def do_get_power(self):
        reply = self._visainstrument.ask('S40')
        if reply.startswith('A4'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if data1 < 104:
                return 'Low'
            if data1 > 112:
                return 'High'
            else:
                return 0
        else:
            print 'Superlum command failed with error: ' + reply
    
    def set_power_low(self):
        if self.get_Optical_Output:
            if self.get_power() == 'Low':
                print 'Power is already low.'
            else:
                reply = self._visainstrument.ask('S41')
        else:
            print 'Can not change the power because the optical output is active.'

    def set_power_high(self):
        if self.get_Optical_Output:
            if self.get_power() == 'High':
                print 'Power is already high.'
            else:
                reply = self._visainstrument.ask('S41')
        else:
            print 'Can not change the power because the optical output is active.'

    def do_get_MASTER_KEY_control(self):
        reply = self._visainstrument.ask('S20')
        if reply.startswith('A2'):
            data1 = int(reply[2:5])
            data2 = int(reply[6:7])
            if data1 < 97:
                return False
            else:
                return True
        elif reply.startswith('AE'):
            print 'MASTER KEY control'
            print 'General error.'
        elif reply.startswith('AL'):
            print 'Instrument is under local control.'

#    def _send_and_read(self, message):
#        logging.debug('Sending %r', message)
#        reply = self._visainstrument.ask(message)
#        return reply

    def set_to_local(self):
        logging.debug('Setting to local.')
        reply = self._visainstrument.ask('S11')
        if reply == 'A11':
            print 'Superlum set to local mode.'
        else:
            print 'Superlum command failed with error: ' + reply

    def do_get_Full_Tuning_Range(self):
        # The Full Tuning range consists of one list, with two lists inside
        # [[end wavelength low power, start wavelength low power, end wavelength high power, start wavelength high power]]
        logging.debug('Getting Full Tuning Range.')
        reply = self._visainstrument.ask('S52')
        if reply.startswith('A52'):
            start_low = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S51')
        if reply.startswith('A51'):
            end_low = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S54')
        if reply.startswith('A54'):
            start_high = int2wvl(int(reply[3:7]))
        reply = self._visainstrument.ask('S53')
        if reply.startswith('A53'):
            end_high = int2wvl(int(reply[3:7]))
        return [[start_low, end_low], [start_high, end_high]]

    def do_get_Operating_Mode(self):
        logging.debug('Getting Operating Mode.')
        reply = self._visainstrument.ask('S60')	    
        if reply.startswith('A6'):
            if reply[2] == '1':
                return 'Manual'
            elif reply[2] == '2':
                return 'Automatic'
            elif reply[2] == '3':
                return 'External'
            elif reply[2] == '4':
                return 'Modulation'

    def do_set_Operating_Mode(self, mode):
        if mode == 'Manual':
            self._visainstrument.write('S61')
        elif mode == 'Automatic':
            self._visainstrument.write('S62')
        elif mode == 'External':
            self._visainstrument.write('S63')
        elif mode == 'Modulation':
            self._visainstrument.write('S64')
        else:
            print 'Mode selection value is wrong, choose either Manual, Automatic, External or Modulation.'

    def set_to_remote(self):
        logging.debug('Setting to remote.')
        reply = self._visainstrument.ask('S12')
        if reply == 'A12':
            print 'Superlum set to remote mode.'
        else:
            print 'Superlum command failed with error: ' + reply

    def do_get_Manual_Mode_Wavelength(self):
        reply = self._visainstrument.ask('S71')
        if reply.startswith('A71'):
            return int2wvl(reply[3:7])

    def do_set_Manual_Mode_Wavelength(self, wvl):
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S81'+laser_string)
        if reply == ('A81'+laser_string):
            print 'Wavelength changed to %4.2f nm' % wvl
        else:
            print 'Error: ' + reply

    def do_get_Sweep_Mode_Start(self):
        reply = self._visainstrument.ask('S72')
        if reply.startswith('A72'):
            return int2wvl(reply[3:7])

    def do_set_Sweep_Mode_Start(self, wvl):
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S82'+laser_string)
        if reply == ('A82'+laser_string):
            print 'Sweep Mode Start changed to %4.2f nm' % wvl
        else:
            print 'Error: ' + reply

    def do_get_Sweep_Mode_End(self):
        reply = self._visainstrument.ask('S73')
        if reply.startswith('A73'):
            return int2wvl(reply[3:7])

    def do_set_Sweep_Mode_End(self, wvl):
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S83'+laser_string)
        if reply == ('A83'+laser_string):
            print 'Sweep Mode End changed to ' + wvl
        else:
            print 'Error: ' + reply

    def do_get_Sweep_Speed(self):
        # If the sweep speed is slow:
        # 2 - 9 nm/s in steps of 1 nm
        # If the sweep speed is fast:
        # 0001 is the 4-byte code for 10 nm/s
        # 1000 is the 4-byte code for 10000 nm/s
        # Steps of 10 nm, so conversion is just multiplication by 10
        reply1 = self._visainstrument.ask('S74')
        reply2 = self._visainstrument.ask('S78')
        if reply1.startswith('A74'):
            if int(reply1[3:7])>0:
                return (10*int(reply1[3:7])) # Fast sweep speed
            else:
                return (reply2[3:5]) # Slow sweep speed


    def do_set_Sweep_Speed(self, speed):
        if speed < 10:
            reply = self._visainstrument.ask('S88'+str(speed))
            if reply.startswith('A88'):
                print 'Fast Sweep Speed set to %d nm/s' % speed
            else:
                print 'Error: ' + reply
        else:
            reply = self._visainstrument.ask('S84'+str(speed/10))
            if reply.startswith('A84'):
                print 'Fast Sweep Speed set to %d nm/s' % speed
            else:
                print 'Error: ' + reply

    def do_get_Modulation_Mode_Wavelength1(self):
        reply = self._visainstrument.ask('S75')
        if reply.startswith('A75'):
            return int2wvl(reply[3:7])

    def do_set_Modulation_Mode_Wavelength1(self, wvl):
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S85'+laser_string)
        if reply == ('A85'+laser_string):
            print 'Modulation Mode Wavelength 1 set to ' + wvl
        else:
            print 'Error: ' + reply

    def do_get_Modulation_Mode_Wavelength2(self):
        reply = self._visainstrument.ask('S76')
        if reply.startswith('A76'):
            return int2wvl(reply[2:6])

    def do_set_Modulation_Mode_Wavelength2(self, wvl):
        laser_string = '%0*d' % (4, wvl2int(wvl))
        reply = self._visainstrument.ask('S86'+laser_string)
        if reply == ('A86'+laser_string):
            print 'Modulation Mode Wavelength 1 set to ' + wvl
        else:
            print 'Error: ' + reply

    def do_get_Modulation_Mode_Frequency(self):
        reply = self._visainstrument.ask('S77')
        if reply.startswith('A77'):
            freq_number = int(reply[3:5])
            return freqs[freq_number-1]
        else:
            print 'Error ' + reply

    def do_set_Modulation_Mode_Frequency(self, freq):
        return None

