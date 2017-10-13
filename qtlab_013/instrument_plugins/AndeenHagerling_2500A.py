# Andeen-Hagerling 2500A driver
#
# Ruben Hofsink <r.hofsink@student.utwente.nl>
# Gabriele de Boo <g.deboo@student.unsw.edu.au>
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
import visa
import types
import logging
import numpy
import time

class AndeenHagerling_2500A(Instrument):
    '''
    WORK IN PROGRESS
    This is the driver for the Andeen-Hagerling 2500 Capacitance Bridge
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'AndeenHagerling_2500A',
                                address='<GPIB address>')
    '''    
    def __init__(self, name, address, reset=False):
        '''
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical', 'measure'])
        
        self._address = address
        RM = visa.ResourceManager()
        self._visainstrument = RM.open_resource(self._address)
        self._visainstrument.read_termination = '\n'
            # Check if connected with serial port? 
            # self._visainstrument.clear()
        
        self.add_parameter('bias_mode',
            flags=Instrument.FLAG_GETSET,
            optionlist = [0,1,2],
            type=types.IntType)
        self.add_parameter('average_mode',
            flags=Instrument.FLAG_GETSET,
            optionlist = range(16),
            type=types.IntType)
        self.add_parameter('measurement_time',
            flags=Instrument.FLAG_SET,
            units='s',
            type=types.FloatType)
        self.add_parameter('alternate_mode',
            flags=Instrument.FLAG_GET,
            type=types.IntType)
        self.add_parameter('cable_length',
            flags=Instrument.FLAG_GET,
            units='m',
            type=types.FloatType)
        self.add_parameter('cable_resistance',
            flags=Instrument.FLAG_GET,
            units='mOhm/m',
            type=types.FloatType)
        self.add_parameter('cable_inductance',
            flags=Instrument.FLAG_GET,
            units='uH/m',
            type=types.FloatType)
        self.add_parameter('cable_capacitance',
            flags=Instrument.FLAG_GET,
            units='pF/m',
            type=types.FloatType)
        self.add_parameter('capacitance',
            flags=Instrument.FLAG_GET,
            units='pF',
            type=types.FloatType)
        self.add_parameter('loss',
            flags=Instrument.FLAG_GET,
            units='depends',
            type=types.FloatType)
        self.add_parameter('loss_units',
            flags=Instrument.FLAG_GETSET,
            type=types.IntType,
            format_map={    1:'nS', 
                            2:'dimensionless dissipation factor', 
                            3:'series resistance in kOhm', 
                            4:'parallel resistance in GOhm', 
                            5:'G per w in jpF'})
        self.add_parameter('excitation_voltage',
            flags=Instrument.FLAG_GET,
            units='V',
            type=types.FloatType)
        self.add_parameter('max_excitation_voltage',
            flags=Instrument.FLAG_GETSET,
            units='V',
            type=types.FloatType)
        self.add_parameter('tracking_mode',
            flags=Instrument.FLAG_GET,
            optionlist = range(6),
            type=types.IntType)
                
        self.add_function('get_single_measurement')
        self.add_function('reset')
        self.add_function('get_all')
        
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:  None
        Output: None
        '''
        logging.info(__name__ + ' : get all')
        self.get_bias_mode()
        self.get_average_mode()
        self.get_alternate_mode()
        self.get_cable_length()
        self.get_cable_resistance()
        self.get_cable_inductance()
        self.get_cable_capacitance()
        self.get_loss_units()
        self.get_single_measurement()
        self.get_max_excitation_voltage()
        self.get_tracking_mode()

    def reset(self):
        '''
        Resets the instrument to default values
        
        Input:  None
        Output: None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('RST')
        self.get_all()
    
    def do_get_tracking_mode(self):
        '''
        Read tracking mode.
        '''
        logging.debug(__name__ + ' : get tracking mode.')
        response = self._visainstrument.query('SHOW TRA')
        return int(response[21])

    def do_get_alternate_mode(self):
        '''
        Read alternate mode.
        '''
        logging.debug(__name__ + ' : get alternate mode.')
        response = self._visainstrument.query('SHOW ALTERNATE')
        return int(response.lstrip('ALTERNATE  ALTEXP='))
    
    def do_set_max_excitation_voltage(self,voltage):
        '''
        Limits the amplitude of the 1 kHz excitation voltage applied to the 
        sample. Any value for the amplitude can be entered, but the bridge 
        will automatically limit the amplitude to a value equal or below the 
        one specified. It will choose a value from the following list:

        [15.00, 7.50, 3.75, 3.00, 1.50, 0.750, 0.375, 0.250, 0.125, 0.100, 
        0.050, 0.030, 0.015, 0.010, 0.0050, 0.0030, 0.0015, 0.0010 or 0.0005] 
        '''
        logging.debug(__name__ + ' : set maximum excitation voltage to '
                                                                 + str(voltage))
        self._visainstrument.write('VOLTAGE ' + str(voltage))

    def do_get_max_excitation_voltage(self):
        '''
        Get the maximum excitation voltage used by the bridge.
        '''
        logging.debug(__name__ + ' : get maximum excitation voltage.')
        response = self._visainstrument.query('SHOW VOLTAGE')
        return float(response[20:28])

    def do_get_loss_units(self):
        '''
        Get units in which the loss is presented.
        '''
        logging.debug(__name__ + ' : get loss units.')
        response = self._visainstrument.query('SHOW UNITS')
        return int(response[13])

    def do_set_loss_units(self,unit):
        '''
        Set the units in which the loss is presented.
        
        Default = 1.

        Input:  1   -   Nanosiemens         -   nS
                2   -   Dissipation factor  -   dimensionless
                3   -   Series resistance   -   kOhm
                4   -   Parallel resistance -   GOhm
                5   -   G/w                 -   jpF
        '''
        logging.debug(__name__ + ' : set loss unit to ' + str(unit))
        self._visainstrument.write('UNITS ' + str(unit))
        
    def do_get_average_mode(self):
        '''
        Read averaging mode.
        '''
        logging.debug(__name__ + ' : get averaging mode.')
        response = self._visainstrument.query('SHOW AVERAGE')
        response = int(response.lstrip('AVERAGE    AVEREXP='))
        mapping = {0:0.04, 1:0.08, 2:0.14, 3:0.25, 4:0.5, 5:1, 6:2, 7:4, 8:8,
                   9:15, 10:30, 11:60, 12:120, 13:250, 14:500, 15:1000}
        self.update_value('measurement_time',mapping[response])
        return response
    
    def do_set_average_mode(self, averagemode):
        '''
        Set averaging mode with corresponding number of samples (NoS) 
        used for averaging and sample time (ST) in seconds. Listed below
        is also the approximate measurement time (MT) in seconds.
        
        Default = 4
                        
        Input:  0   -   NoS: 1      ST: 0.01    MT: 0.04
                1   -   NoS: 1      ST: 0.05    MT: 0.08
                2   -   NoS: 1      ST: 0.10    MT: 0.14
                3   -   NoS: 2      ST: 0.10    MT: 0.25
                4   -   NoS: 4      ST: 0.10    MT: 0.5
                5   -   NoS: 8      ST: 0.10    MT: 1
                6   -   NoS: 16     ST: 0.10    MT: 2
                7   -   NoS: 32     ST: 0.10    MT: 4
                8   -   NoS: 64     ST: 0.10    MT: 8
                9   -   NoS: 128    ST: 0.10    MT: 15
                10  -   NoS: 256    ST: 0.10    MT: 30
                11  -   NoS: 512    ST: 0.10    MT: 60
                12  -   NoS: 1024   ST: 0.10    MT: 120
                13  -   NoS: 2048   ST: 0.10    MT: 250
                14  -   NoS: 4096   ST: 0.10    MT: 500
                15  -   NoS: 8192   ST: 0.10    MT: 1000
        
        Output: None
        '''
        logging.debug(__name__ + ' : set average mode to ' + str(averagemode))
        self._visainstrument.write('AV ' + str(averagemode))
        mapping = {0:0.04, 1:0.08, 2:0.14, 3:0.25, 4:0.5, 5:1, 6:2, 7:4, 8:8,
                   9:15, 10:30, 11:60, 12:120, 13:250, 14:500, 15:1000}
        self.set_measurement_time(mapping[averagemode])
    
    def do_set_measurement_time(self, meastime):
        '''
        Set approximated measurement time. 
        Conditional on value of Averaging Mode. This parameter is used to set
        waiting time between measurements.
        '''
        logging.debug(__name__ + ' : set approximate measurement time')
        
    def do_get_bias_mode(self):
        '''
        Read status of external bias and internal resistor.
        '''     
        logging.debug(__name__ + ' : get bias mode.')
        response = self._visainstrument.query('SHOW BIAS')
        return int(response.lstrip('DC BIAS    ENABLE='))

    def do_set_bias_mode(self, biasmode):
        '''
        Enable or disable user-supplied DC bias voltage
        This also selects the value of an internal resistor placed in series
        
        Input:  0   -   Disabled
                1   -   Enabled with 100 megohm resistor
                2   -   Enabled with 1 megohm resistor

        Output: None
        '''
        logging.debug(__name__ + ' : enable/disable bias voltage to mode '
                      + str(biasmode))
        self._visainstrument.write('BIAS ' + str(biasmode))
    
    def do_get_cable_length(self):
        '''
        Get compensated cable length in meters.

        Default is 1.00.
        '''
        logging.debug(__name__ + ' : get cable length.')
        result = self._visainstrument.query('SH CAB')
        return float(result[19:26])
    
    def do_get_cable_resistance(self):
        '''
        Get compensated cable resistance in milliohms per meter.

        Default is 40.
        '''
        logging.debug(__name__ + ' : get cable resistance.')
        result = self._visainstrument.query('SH CAB')
        while not 'RESIS' in result: #Weird error, bad solution, but works.
            result = self._visainstrument.read()
        return float(result[25:32])

    def do_get_cable_inductance(self):
        '''
        Get compensated cable inductance in microhenries per meter.

        Default is 1.10.
        '''
        logging.debug(__name__ + ' : get cable inductance.')
        x = self._visainstrument.query('SH CAB')
        x = self._visainstrument.read()
        result = self._visainstrument.read()
        return float(result[25:31])

    def do_get_cable_capacitance(self):
        '''
        Get compensated cable capacitance in picofahrads per meter.

        Default is 70.0.
        '''
        logging.debug(__name__ + ' : get cable inductance.')
        x = self._visainstrument.query('SH CAB')
        x = self._visainstrument.read()
        x = self._visainstrument.read()
        result = self._visainstrument.read()
        return float(result[26:32])


    def get_single_measurement(self):
        '''
        Get a single measurement
        Returns a tuple of capacitance, loss and excitation voltage
        '''
        logging.debug(__name__ + ' : take single measurement.')
        av_mode = self.get_average_mode()
        self._visainstrument.write('SINGLE')
        if av_mode > 5:
            mapping = {0:0.04, 1:0.08, 2:0.14, 3:0.25, 4:0.5, 5:1, 6:2, 7:4,
                       8:8, 9:15, 10:30, 11:60, 12:120, 13:250, 14:500, 15:1000}
            self._visainstrument.timeout = (mapping[av_mode] * 2000)
        result = self._visainstrument.read()
        self._visainstrument.timeout = 3000
        if not '=' in result:   #checks if there is an error
            if result == 'CAP TOO HIGH':
                logging.error(__name__ + ' : Unknown capacitance too high. '+
                              'Most positive measurable capacitance is 1.2 uF.')
                return 0
            elif result == 'CAP TOO NEG':
                logging.error(__name__ + ' : Unknown capacitance too low. '+ 
                            'Most negative measurable capacitance is -0.12 uF.')
                return 0
            elif result == 'AC ON L INPUT':
                logging.error(__name__ + ' : Too much externally generated noise'
      + ' below 100 Hz sensed at measurement terminals. Check for AC coupling.')
                return 0
            elif result == 'DC ON L INPUT':
                logging.error(__name__ + ' : There is an unallowable DC '+ 
      'component on the LOW terminal. If on purpose, check if BIAS is enabled.')
                return 0
            elif result == 'ERRATIC INPUT':
                logging.error(__name__ + ' : Software is unable to balance the '
                     + 'bridge due to excess noise or rapidly changing sample.')
                return 0
            elif result == 'EXCESS NOISE':
                logging.error(__name__ + ' : Too much externally generated noise'
                           +' near 1 kHz is picked up at measurement terminals')
                return 0
            elif result == 'H TO L SHORT':
                logging.error(__name__ + ' : Impedance between HIGH and LOW '+
                              'is too low. Check if terminals are not shorted.')
                return 0
            elif result == 'H TO GND SHORT':
                logging.error(__name__ + ' : Check if HIGH to Ground is not shorted.')
                return 0
            elif result == 'INDETERM SCALE':
                logging.error(__name__ + ' : Unknown impedance appears '+
                                             'to be off-scale.')
                return 0
            elif result == 'L TO GND SHORT':
                logging.error(__name__ + ' : Impedance between LOW and GND too '
                                       +'small. Check if they are not shorted.')
                return 0
            elif result == 'LOSS TOO HIGH':
                logging.error(__name__ + ' : Loss too high. Most positive '+
                                         'measurable conductance is 60,000 nS.')
                return 0
            elif result == 'LOSS TOO NEG':
                logging.error(__name__ + ' : Loss too negative. Most negative '+
                                          'measurable conductance is -6000 nS.')
                return 0
        else: 
            C = float(result[3:14])
            L = float(result[21:32])
            V = float(result[39:46])
            self.update_value('capacitance', C)
            self.update_value('loss', L)
            self.update_value('excitation_voltage', V)
            if "OVEN" in result:
                logging.warning(__name__ + ' : Measurement conducted while the oven was not ready.')
            return C, L, V

    def do_get_capacitance(self):
        '''
        Get capacitance from function 'get_single_measurement'.
        '''
        logging.debug(__name__ + ' : get capacitance')
        C, L, V = self.get_single_measurement()
        return C

    def do_get_loss(self):
        '''
        Get loss from function 'get_single_measurement'.
        '''
        logging.debug(__name__ + ' : get loss')
        C, L, V = self.get_single_measurement()
        return L
    
    def do_get_excitation_voltage(self):
        '''
        Get excitation voltage from function 'get_single_measurement'.
        '''
        logging.debug(__name__ + ' : get excitation voltage')
        C, L, V = self.get_single_measurement()
        return V




