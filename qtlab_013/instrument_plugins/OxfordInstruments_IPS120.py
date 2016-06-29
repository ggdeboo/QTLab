# OxfordInstruments_IPS120.py class, to perform the communication between the Wrapper and the device
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
# Sam Hile <samhile@gmail.com> 2011
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
from time import time
import visa
import types
import logging
import qt

class OxfordInstruments_IPS120(Instrument):
    '''
    This is the python driver for the Oxford Instruments IPS 120 Magnet Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_IPS120', address='<Instrument address>')
    <Instrument address> = ASRL1::INSTR / COMx

    Note: Since the ISOBUS allows for several instruments to be managed in parallel, the command
    which is sent to the device starts with '@n', where n is the ISOBUS instrument number.

    '''
#TODO: auto update script
#TODO: get doesn't always update the wrapper! (e.g. when input is an int and output is a string)

    def __init__(self, name, address, number=2):
        '''
        Initializes the Oxford Instruments IPS 120 Magnet Power Supply.

        Input:
            name (string)    : name of the instrument
            address (string) : instrument address
            number (int)     : ISOBUS instrument number

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._number = number
        self._visainstrument = visa.instrument(self._address)
        self._values = {}
        self._visainstrument.stop_bits = 2
        self._visainstrument.delay = 20e-3

        #Add parameters
        self.add_parameter('mode', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Amps, Magnet sweep: fast",
            1 : "Tesla, Magnet sweep: fast",
            4 : "Amps, Magnet sweep: slow",
            5 : "Tesla, Magnet sweep: slow",
            8 : "Amps, (Magnet sweep: unaffected)",
            9 : "Tesla, (Magnet sweep: unaffected)"})
        self.add_parameter('mode2', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {
            0 : "At rest",
            1 : "Sweeping",
            2 : "Sweep limiting",
            3 : "Sweeping & sweep limiting"})
        self.add_parameter('activity', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Hold",
            1 : "To set point",
            2 : "To zero",
            4 : "Clamped"})
        self.add_parameter('switch_heater', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Off magnet at zero (switch closed)",
            1 : "On (switch open)",
            2 : "Off magnet at field (switch closed)",
            5 : "Heater fault (heater is on but current is low)",
            8 : "No switch fitted"})
        self.add_parameter('polarity', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('field_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-11.9465, maxval=11.9465)
        self.add_parameter('sweeprate_field', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=1.0)
        self.add_parameter('current_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-116.10, maxval=116.10)
        self.add_parameter('sweeprate_current', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=0, maxval=9.718)
        self.add_parameter('remote_status', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",
            4 : "Auto-run-down",
            5 : "Auto-run-down",
            6 : "Auto-run-down",
            7 : "Auto-run-down"})
        self.add_parameter('system_status', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {
            0 : "Normal",
            1 : "Quenched",
            2 : "Over Heated",
            4 : "Warming Up",
            8 : "Fault"})
        self.add_parameter('system_status2', type=types.IntType,
            flags=Instrument.FLAG_GET,
            format_map = {
            0 : "Normal",
            1 : "On positive voltage limit",
            2 : "On negative voltage limit",
            4 : "Outside negative current limit",
            8 : "Outside positive current limit"
            })
        self.add_parameter('current', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('voltage', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('magnet_current', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('field', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('voltage_limit', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('persistent_current', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('trip_current', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('persistent_field', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('trip_field', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('heater_current', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('current_limit_upper', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('current_limit_lower', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('lead_resistance', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('magnet_inductance', type=types.FloatType,
            flags=Instrument.FLAG_GET)

        # Add functions
        self.add_function('get_all')
        self.add_function('ramp_field_to')
        self.add_function('ramp_field_to_zero')
        self.add_function('init_magnet')
        self.add_function('into_persistent')
        self.add_function('outof_persistent')

        #call some
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : reading all settings from instrument')
        self.get_remote_status()
        self.get_system_status()
        self.get_system_status2()
        self.get_current()
        self.get_voltage()
        self.get_magnet_current()
        self.get_current_setpoint()
        self.get_sweeprate_current()
        self.get_field()
        self.get_field_setpoint()
        self.get_sweeprate_field()
        self.get_voltage_limit()
        self.get_persistent_current()
        self.get_trip_current()
        self.get_persistent_field()
        self.get_trip_field()
        self.get_heater_current()
        self.get_current_limit_upper()
        self.get_current_limit_lower()
        self.get_lead_resistance()
        self.get_magnet_inductance()
        self.get_mode()
        self.get_activity()
        self.get_polarity()
        self.get_switch_heater()

    # Set magnetic field
    def ramp_field_to(self,value):
        if (abs(self.get_field()-value) >= 0.00001):
            if not self.get_activity()==0:
                self.hold()
            if not self.get_switch_heater()==1:
                self.heater_on()
                if not self.get_switch_heater() == 1:
                    logging.info(__name__ + ' : Unable to switch heat on!')
            self.set_field_setpoint('{0:2.4f}'.format(value))
            self.to_setpoint()
            #print 'Sweeping magnetic field to %2.4f Tesla...' % value
            while abs(self.get_field()-value) >= 0.00001:
                qt.msleep(5)
            self.hold()
            logging.info('Desired field reached. Wait 10s for the output ' +
                            'voltage to stabilize.')
            qt.msleep(10)
            # wait time of 10s was added by Chunming after seeing a small quench event.
        else:
            logging.info('Magnet already at set field.')

    #persistent mode
    def into_persistent(self):
        logging.info('Wait 5s before switching heater.')
        qt.msleep(5)
        if not self.get_activity()==0:
            self.hold()
        if self.get_switch_heater()==1:
            self.heater_off()
        logging.info('Wait 40s more for superconducting.')
        qt.msleep(40)   #added by Chunming, wait 60s for heater off. 30s recommonded by the manual.
        self.to_zero()
        logging.info('Into persistent mode: Sweeping leads to zero...')
        while abs(self.get_field()) >= 0.00001:
            qt.msleep(1)
        self.hold()
        value = self.get_persistent_field()  
        logging.info('Leads at zero. Persistent field {0:2.4f} Tesla.'.format(value))
        
    def outof_persistent(self):
        logging.info('Wait 5s before resuming the current.')
        qt.msleep(5)
        if not self.get_activity()==0:
            self.hold()
        persfield = self.get_persistent_field()
        if not persfield == self.get_field_setpoint():
            self.set_field_setpoint('%2.4f' % persfield)
        self.to_setpoint()
        logging.info('Sweeping leads to persistent value...')
        while abs(self.get_field() - persfield) >= 0.00001:
            qt.msleep(1)
        qt.msleep(5)
        self.heater_on()
        self.hold()    
        logging.info('Out of persistent mode.')

    # Set magnetic field to zero
    def ramp_field_to_zero(self):
        if not self.get_activity()==0:
            self.hold()
        if not self.get_switch_heater()==1:
            self.heater_on()
        self.set_sweeprate_field(0.1)
        self.to_zero()
        logging.info('Sweeping magnetic field quickly to zero...')
        while abs(self.get_field()) >= 0.00001:
            qt.msleep(1)

        self.hold()    
        logging.info('Field at zero.')

    # Initialize magnet and put into high resolution
    def init_magnet(self,sweeprate=0.1):
        '''
        Initializes magnet and puts it into high resolution.
        '''
        self.get_all()
        self.remote()
        self.hold()
        self._write('Q4')
        self.set_sweeprate_field('%2.4f' % sweeprate)
        if not self.get_activity()==0:
            self.hold()


    # Functions
    def _execute(self, message):
        '''
        Write a command to the device

        Input:
            message (str) : write command for the device

        Output:
            None
        '''
        logging.info(__name__ + ' : Send the following command to the device: %s' % message)
        result = self._visainstrument.ask('@%s%s' % (self._number, message))
        if result.find('?') >= 0:
            logging.error("Error: Command {0} not recognized".format(message))
        else:
            return result
        
    def _write(self, message):
        '''
        Write a command to the device, no response (for Q command)

        Input:
            message (str) : write command for the device

        Output:
            None
        '''
        logging.info(__name__ + ' : Send the following command to the ' + 
                        'device: {0}'.format(message))
        self._visainstrument.write('@%s%s' % (self._number, message))


    def identify(self):
        '''
        Identify the device

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Identify the device')
        return self._execute('V')

    def examine(self):
        '''
        Examine the status of the device

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Examine status')

        print 'System Status: '
        print self.get_system_status()

        print 'Activity: '
        print self.get_activity()

        print 'Local/Remote status: '
        print self.get_remote_status()

        print 'Switch heater: '
        print self.get_switch_heater()

        print 'Mode: '
        print self.get_mode()

        print 'Polarity: '
        print self.get_polarity()

    def remote(self):
        '''
        Set control to remote & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to remote & locked')
        self.set_remote_status(3)

    def local(self):
        '''
        Set control to local & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to local & locked')
        self.set_remote_status(0)

    def do_get_remote_status(self):
        '''
        Get remote control status

        Input:
            None

        Output:
            result(str) :
            "Local & locked",
            "Remote & locked",
            "Local & unlocked",
            "Remote & unlocked",
            "Auto-run-down",
            "Auto-run-down",
            "Auto-run-down",
            "Auto-run-down"
        '''
        logging.info(__name__ + ' : Get remote control status')
        result = self._execute('X')
        return int(result[6])

    def do_set_remote_status(self, mode):
        '''
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        '''
        status = {
        0 : "Local and locked",
        1 : "Remote and locked",
        2 : "Local and unlocked",
        3 : "Remote and unlocked",
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting remote control status to %s' % status.get(mode,"Unknown"))
            self._execute('C%s' % mode)
        else:
            print 'Invalid mode inserted: %s' % mode

    def do_get_system_status(self):
        '''
        Get the system status

        Input:
            None

        Output:
            result (str) :
            "Normal",
            "Quenched",
            "Over Heated",
            "Warming Up",
            "Fault"
        '''
        result = self._execute('X')
        logging.info(__name__ + ' : Getting system status')
        return int(result[1])

    def do_get_system_status2(self):
        '''
        Get the system status

        Input:
            None

        Output:
            result (str) :
            "Normal",
            "On positive voltage limit",
            "On negative voltage limit",
            "Outside negative current limit",
            "Outside positive current limit"
        '''
        result = self._execute('X')
        logging.info(__name__ + ' : Getting system status')
        return int(result[2])

    def do_get_current(self):
        '''
        Demand output current of device

        Input:
            None

        Output:
            result (float) : output current in Amp
        '''
        logging.info(__name__ + ' : Read output current')
        result = self._execute('R0')
        return float(result.replace('R',''))

    def do_get_voltage(self):
        '''
        Demand measured output voltage of device

        Input:
            None

        Output:
            result (float) : output voltage in Volt
        '''
        logging.info(__name__ + ' : Read output voltage')
        result = self._execute('R1')
        return float(result.replace('R',''))

    def do_get_magnet_current(self):
        '''
        Demand measured magnet current of device

        Input:
            None

        Output:
            result (float) : measured magnet current in Amp
        '''
        logging.info(__name__ + ' : Read measured magnet current')
        result = self._execute('R2')
        return float(result.replace('R',''))

    def do_get_current_setpoint(self):
        '''
        Return the set point (target current)

        Input:
            None

        Output:
            result (float) : Target current in Amp
        '''
        logging.info(__name__ + ' : Read set point (target current)')
        result = self._execute('R5')
        return float(result.replace('R',''))

    def do_set_current_setpoint(self, current):
        '''
        Set current setpoint (target current)
        Input:
            current (float) : target current in Amp

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting target current to %s' % current)
        self._execute('I{0:3.3f}'.format(current))
        self.get_field_setpoint() # Update field setpoint

    def do_get_sweeprate_current(self):
        '''
        Return sweep rate (current)

        Input:
            None

        Output:
            result (float) : sweep rate in Amp/min
        '''
        logging.info(__name__ + ' : Read sweep rate (current)')
        result = self._execute('R6')
        return float(result.replace('R',''))

    def do_set_sweeprate_current(self, sweeprate):
        '''
        Set sweep rate (current)

        Input:
            sweeprate(float) : Sweep rate in Amps/min.

        Output:
            None
        '''
        logging.info(__name__ + ' : Set sweep rate (current) to %s Amps/min' % sweeprate)
        self._execute('S{0:1.3f}'.format(sweeprate))
        self.get_sweeprate_field() # Update sweeprate_field

    def do_get_field(self):
        '''
        Demand output field

        Input:
            None

        Output:
            result (float) : Output field in Tesla
        '''
        logging.info(__name__ + ' : Read output field')
        result = self._execute('R7')
        return float(result.replace('R',''))

    def do_get_field_setpoint(self):
        '''
        Return the set point (target field)

        Input:
            None

        Output:
            result (float) : Field set point in Tesla
        '''
        logging.info(__name__ + ' : Read field set point')
        result = self._execute('R8')
        return float(result.replace('R',''))

    def do_set_field_setpoint(self, field):
        '''
        Set the field set point (target field)
        Input:
            field (float) : target field in Tesla

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting target field to %s' % field)
        self._execute('J{0:2.4f}'.format(field))
        self.get_current_setpoint() #Update current setpoint

    def do_get_sweeprate_field(self):
        '''
        Return sweep rate (field)

        Input:
            None

        Output:
            result (float) : sweep rate in Tesla/min
        '''
        logging.info(__name__ + ' : Read sweep rate (field)')
        result = self._execute('R9')
        return float(result.replace('R',''))

    def do_set_sweeprate_field(self, sweeprate):
        '''
        Set sweep rate (field)

        Input:
            sweeprate(float) : Sweep rate in Tesla/min.

        Output:
            None
        '''
        logging.info(__name__ + ' : Set sweep rate (field) to %s Tesla/min' % sweeprate)
        self._execute('T{0:1.4f}'.format(sweeprate))
        self.get_sweeprate_current() # Update sweeprate_current

    def do_get_voltage_limit(self):
        '''
        Return voltage limit

        Input:
            None

        Output:
            result (float) : voltage limit in Volt
        '''
        logging.info(__name__ + ' : Read voltage limit')
        result = self._execute('R15')
        result = float(result.replace('R',''))
        self.set_parameter_bounds('voltage',-result,result)
        return result

    def do_get_persistent_current(self):
        '''
        Return persistent magnet current

        Input:
            None

        Output:
            result (float) : persistent magnet current in Amp
        '''
        logging.info(__name__ + ' : Read persistent magnet current')
        result = self._execute('R16')
        return float(result.replace('R',''))

    def do_get_trip_current(self):
        '''
        Return trip current

        Input:
            None

        Output:
            result (float) : trip current om Amp
        '''
        logging.info(__name__ + ' : Read trip current')
        result = self._execute('R17')
        return float(result.replace('R',''))

    def do_get_persistent_field(self):
        '''
        Return persistent magnet field

        Input:
            None

        Output:
            result (float) : persistent magnet field in Tesla
        '''
        logging.info(__name__ + ' : Read persistent magnet field')
        result = self._execute('R18')
        return float(result.replace('R',''))

    def do_get_trip_field(self):
        '''
        Return trip field

        Input:
            None

        Output:
            result (float) : trip field in Tesla
        '''
        logging.info(__name__ + ' : Read trip field')
        result = self._execute('R19')
        return float(result.replace('R',''))

    def do_get_heater_current(self):
        '''
        Return switch heater current

        Input:
            None

        Output:
            result (float) : switch heater current in milliAmp
        '''
        logging.info(__name__ + ' : Read switch heater current')
        result = self._execute('R20')
        return float(result.replace('R',''))

    def do_get_current_limit_upper(self):
        '''
        Return safe current limit, most positive

        Input:
            None

        Output:
            result (float) : safe current limit, most positive in Amp
        '''
        logging.info(__name__ + ' : Read safe current limit, most positive')
        result = self._execute('R22')
        return float(result.replace('R',''))

    def do_get_current_limit_lower(self):
        '''
        Return safe current limit, most negative

        Input:
            None

        Output:
            result (float) : safe current limit, most negative in Amp
        '''
        logging.info(__name__ + ' : Read safe current limit, most negative')
        result = self._execute('R21')
        return float(result.replace('R',''))

    def do_get_lead_resistance(self):
        '''
        Return lead resistance

        Input:
            None

        Output:
            result (float) : lead resistance in milliOhm
        '''
        logging.info(__name__ + ' : Read lead resistance')
        result = self._execute('R23')
        return float(result.replace('R',''))

    def do_get_magnet_inductance(self):
        '''
        Return magnet inductance

        Input:
            None

        Output:
            result (float) : magnet inductance in Henry
        '''
        logging.info(__name__ + ' : Read magnet inductance')
        result = self._execute('R24')
        return float(result.replace('R',''))

    def do_get_activity(self):
        '''
        Get the activity of the magnet. Possibilities: Hold, Set point, Zero or Clamp.
        Input:
            None

        Output:
            result(str) : "Hold", "Set point", "Zero" or "Clamp".
        '''
        result = self._execute('X')
        logging.info(__name__ + ' : Get activity of the magnet.')
        return int(result[4])

    def do_set_activity(self, mode):
        '''
        Set the activity to Hold, To Set point or To Zero.

        Input:
            mode (int) :
            0 : "Hold",
            1 : "To set point",
            2 : "To zero"

            4 : "Clamped" (not included)

        Output:
            None
        '''
        status = {
        0 : "Hold",
        1 : "To set point",
        2 : "To zero"
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting magnet activity to %s' % status.get(mode, "Unknown"))
            self._execute('A%s' % mode)
        else:
            print 'Invalid mode inserted.'

    def hold(self):
        '''
        Set the device activity to "Hold"
        Input:
            None
        Output:
            None
        '''
        self.set_activity(0)
        self.get_activity()

    def to_setpoint(self):
        '''
        Set the device activity to "To set point". This initiates a sweep.
        Input:
            None
        Output:
            None
        '''
        self.set_activity(1)
        self.get_activity()

    def to_zero(self):
        '''
        Set the device activity to "To zero". This sweeps te magnet back to zero.
        Input:
            None
        Output:
            None
        '''
        self.set_activity(2)
        self.get_activity()

    def do_get_switch_heater(self):
        '''
        Get the switch heater status.
        Input:
            None

        Output:
            result(str) : "Off magnet at zero", "On (switch open)", "Off magnet at field (switch closed)",
            "Heater fault (heater is on but current is low)" or "No switch fitted".
        '''
        logging.info(__name__ + ' : Get switch heater status')
        result = self._execute('X')
        return int(result[8])

    def do_set_switch_heater(self, mode):
        '''
        Set the switch heater Off or On. Note: After issuing a command it is necessary to wait
        several seconds for the switch to respond.
        Input:
            mode (int) :
            0 : "Off",
            1 : "On, if PSU = Magnet",

            2 : "On, No checks" (not available)

        Output:
            None
        '''
        status = {
        0 : "Off",
        1 : "On, if PSU = Magnet"
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting switch heater to %s' % status.get(mode, "Unknown"))
            self._execute('H%s' % mode)
            print "Setting switch heater... (wait 20s)"
            qt.msleep(20)
            print '...OK'
        else:
            print 'Invalid mode inserted.'

    def heater_on(self):
        '''
        Switch the heater on, with PSU = Magnet current check
        Input:
            None
        Output:
            None
        '''
        self.set_switch_heater(1)
        self.get_switch_heater()

    def heater_off(self):
        '''
        Switch the heater off
        Input:
            None
        Output:
            None
        '''
        self.set_switch_heater(0)
        self.get_switch_heater()

    def do_get_mode(self):
        '''
        Get the Mode of the device
        Input:
            None

        Output:
            "Amps, Magnet sweep: fast",
            "Tesla, Magnet sweep: fast",
            "Amps, Magnet sweep: slow",
            "Tesla, Magnet sweep: slow"
        '''
        logging.info(__name__ + ' : Get device mode')
        result = self._execute('X')
        return int(result[10])

    def do_get_mode2(self):
        '''
        Get the Mode of the device
        Input:
            None

        Output:
            "At rest",
            "Sweeping",
            "Sweep limiting",
            "Sweeping & sweep limiting"
        '''
        logging.info(__name__ + ' : Get device mode')
        result = self._execute('X')
        return int(result[11])

    def do_set_mode(self, mode):
        '''
        Input:
            mode(int):
            0 : "Amps, Magnet sweep: fast",
            1 : "Tesla, Magnet sweep: fast",
            4 : "Amps, Magnet sweep: slow",
            5 : "Tesla, Magnet sweep: slow"
            8 : "Amps, (Magnet sweep: unaffected)",
            9 : "Tesla, (Magnet sweep: unaffected)"

        Output:
            None
        '''
        status = {
        0 : "Amps, Magnet sweep: fast",
        1 : "Tesla, Magnet sweep: fast",
        4 : "Amps, Magnet sweep: slow",
        5 : "Tesla, Magnet sweep: slow",
        8 : "Amps, (Magnet sweep: unaffected)",
        9 : "Tesla, (Magnet sweep: unaffected)"
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting device mode to %s' % status.get(mode, "Unknown"))
            self._execute('M%s' % mode)
        else:
            print 'Invalid mode inserted.'

    def do_set_polarity(self,mode1,mode2):
        '''
        Set the polarity of the output current (untested! -sam)
        This is a function for backwards compatibility with the PS120, it
        should not be used with the IPS120 supply as it will go to negative
        fields by itself.

        Input:
            Mode1 (int):
        0 : "Desired: Positive, Magnet: Positive, Commanded: Positive",
        1 : "Desired: Positive, Magnet: Positive, Commanded: Negative",
        2 : "Desired: Positive, Magnet: Negative, Commanded: Positive",
        3 : "Desired: Positive, Magnet: Negative, Commanded: Negative",
        4 : "Desired: Negative, Magnet: Positive, Commanded: Positive",
        5 : "Desired: Negative, Magnet: Positive, Commanded: Negative",
        6 : "Desired: Negative, Magnet: Negative, Commanded: Positive",
        7 : "Desired: Negative, Magnet: Negative, Commanded: Negative"
            Mode2 (int):
        1 : "Negative contactor closed",
        2 : "Positive contactor closed",
        3 : "Both contactors open",
        4 : "Both contactors closed"

        Output:
            None
        '''
        status1 = {
        0 : "Desired: Positive, Magnet: Positive, Commanded: Positive",
        1 : "Desired: Positive, Magnet: Positive, Commanded: Negative",
        2 : "Desired: Positive, Magnet: Negative, Commanded: Positive",
        3 : "Desired: Positive, Magnet: Negative, Commanded: Negative",
        4 : "Desired: Negative, Magnet: Positive, Commanded: Positive",
        5 : "Desired: Negative, Magnet: Positive, Commanded: Negative",
        6 : "Desired: Negative, Magnet: Negative, Commanded: Positive",
        7 : "Desired: Negative, Magnet: Negative, Commanded: Negative"
        }
        status2 = {
        1 : "Negative contactor closed",
        2 : "Positive contactor closed",
        3 : "Both contactors open",
        4 : "Both contactors closed"
        }
        if status1.__contains__(mode1) and status2.__contains__(mode2):
            logging.info(__name__ + ' : Setting device polarity mode1 to %s' % status.get(mode, "Unknown"))
            logging.info(__name__ + ' : Setting device polarity mode2 to %s' % status.get(mode, "Unknown"))
            self._execute('X%s' % (mode1 + mode2))
        else:
            print 'Invalid mode inserted.'

    def do_get_polarity(self):
        '''
        Get the polarity of the output current
        Input:
            None

        Output:
            result (str) :
            "Desired: Positive, Magnet: Positive, Commanded: Positive",
            "Desired: Positive, Magnet: Positive, Commanded: Negative",
            "Desired: Positive, Magnet: Negative, Commanded: Positive",
            "Desired: Positive, Magnet: Negative, Commanded: Negative",
            "Desired: Negative, Magnet: Positive, Commanded: Positive",
            "Desired: Negative, Magnet: Positive, Commanded: Negative",
            "Desired: Negative, Magnet: Negative, Commanded: Positive",
            "Desired: Negative, Magnet: Negative, Commanded: Negative"
        '''
        status1 = {
        0 : "Desired: Positive, Magnet: Positive, Commanded: Positive",
        1 : "Desired: Positive, Magnet: Positive, Commanded: Negative",
        2 : "Desired: Positive, Magnet: Negative, Commanded: Positive",
        3 : "Desired: Positive, Magnet: Negative, Commanded: Negative",
        4 : "Desired: Negative, Magnet: Positive, Commanded: Positive",
        5 : "Desired: Negative, Magnet: Positive, Commanded: Negative",
        6 : "Desired: Negative, Magnet: Negative, Commanded: Positive",
        7 : "Desired: Negative, Magnet: Negative, Commanded: Negative"
        }
        status2 = {
        1 : "Negative contactor closed",
        2 : "Positive contactor closed",
        3 : "Both contactors open",
        4 : "Both contactors closed"
        }
        logging.info(__name__ + ' : Get device polarity')
        result = self._execute('X')
        return status1.get(int(result[13]), "Unknown") + ", " + status2.get(int(result[14]), "Unknown")

    def get_changed(self):
        print "Current: "
        print self.get_current()
        print "Field: "
        print self.get_field()
        print "Magnet current: "
        print self.get_magnet_current()
        print "Heater current: "
        print self.get_heater_current()
        print "Mode: "
        print self.get_mode()
