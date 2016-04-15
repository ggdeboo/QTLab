# Driver for Agilent 53131A
# Shouyi Xie <shouyixie89@gmail.com>
# Gabriele de Boo <ggdeboo@gmail.com>
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

import qt


class Agilent_53131A(Instrument):
    '''
    This is the driver for the Agilent 53131A frequency counter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Agilent_53131A',
        address='<GBIP address>',
        reset=<bool>,
    '''

    def __init__(self, name, address, reset=True,):
        '''
        Initializes the Agilent_53131A, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Agilent_53131A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        if self._visainstrument.interface_type == 4:
            self._visainstrument.baud_rate = 19200
            self._visainstrument.term_chars = '\r'


# --------------------------------------
#           parameters
# --------------------------------------

        self.add_parameter('measurement_function',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
            )
        self.add_parameter('measure_freq',
            type=types.StringType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_SET,
            option_list=('FUNC','CONF'))
        self.add_parameter('initiate',
            type=types.StringType,
            flags=Instrument.FLAG_SET,
            option_list=('CONTINUOUS','SINGLE'))
        self.add_parameter('freq',
            type=types.FloatType,
            channels=('read', 'fetch'), channel_prefix='%s_',
            flags=Instrument.FLAG_GET)
        self.add_parameter('freq_ratio_1to2',
            type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('freq_ratio_2to1',
            type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('arming',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('AUTO','DIGITS','TIME'))
        self.add_parameter('arming_digits',
            type=types.IntType,
            flags=Instrument.FLAG_GETSET,
            minval=3, maxval=15)
        self.add_parameter('arming_time',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            minval=0.001, maxval=1000)
        self.add_parameter('auto_trigger',
            type=types.BooleanType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET)    
        self.add_parameter('trigger_level',
            type=types.FloatType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET,)    
        self.add_parameter('slope',
            type=types.StringType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET,
            option_list=('POS','NEG'))
        self.add_parameter('sensitivity',
            type=types.StringType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET,
            option_list=('HI','MED','LOW'))
        self.add_parameter('impedance',
            type=types.FloatType, units='Ohm',
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('coupling',
            type=types.StringType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET,
            option_list=('DC','AC'))
        self.add_parameter('attenuation',
            type=types.FloatType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('filter',
            type=types.BooleanType,
            channels=(1, 2), channel_prefix='ch%d_',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('upper_limit',
            type=types.FloatType, units='Hz',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('lower_limit',
            type=types.FloatType, units='Hz',
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('limit_state',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('on_fail',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('STOP','GO_ON'))
        self.add_parameter('limit_display',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('GRAPH','NUMBER'))
        self.add_parameter('stats_display',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('STD_DEV','MEAN','MAX','MIN','MEAS'))
        self.add_parameter('stats_count',
            type=types.IntType,units='#', minval=2, maxval=1e6,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('stats_state',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('stats_use',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('ALL_MEAS','IN_LIMIT'))
        self.add_parameter('stats_on_single',
            type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            option_list=('1','N'))
        self.add_parameter('scale',
            type=types.FloatType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('offset',
            type=types.FloatType, minval=-9.999999e12, maxval=9.999999e12,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('math_state',
            type=types.BooleanType,
            flags=Instrument.FLAG_GETSET)

        # timebase
        self.add_parameter('timebase',
            type=types.StringType,
            flags=Instrument.FLAG_GET,
            format_map={'INT':'internal',
                        'EXT':'external'})


        self.get_all()

# --------------------------------------
#           functions
# --------------------------------------

# Measure keys
    def get_all(self):
        self.get_measurement_function()
        self.get_timebase()
        for channel in ['ch1','ch2']:
            self.get('{0}_attenuation'.format(channel))
            self.get('{0}_coupling'.format(channel))
            self.get('{0}_filter'.format(channel))
            self.get('{0}_impedance'.format(channel))
            self.get('{0}_sensitivity'.format(channel))
            self.get('{0}_trigger_level'.format(channel))
            self.get('{0}_slope'.format(channel))

    def do_get_measurement_function(self):
        response = self._visainstrument.ask(':SENS:FUNC?')
        return response

    def do_set_measure_freq(self, val, channel):
        if val == 'FUNC':
            self._visainstrument.write('FUNC "FREQ %s"' % channel)
            # Configure the instrument to perform frequency measurement.
            # Does not affect arming mode or ':INIT:CONT' state.
        elif val == 'CONF':
            self._visainstrument.write(':CONF:FREQ (@%s)' % channel)
            # Configure the instrument to perform frequency measurement 
            # (and sets the expected frequency and resolution).
            # Arming mode is automatically changed to 'DIGITS' by this command.
            # Does not affect the ':INIT:CONT' state.

    def do_set_initiate(self, val):
        if val == 'CONTINUOUS':
            self._visainstrument.write(':INIT:CONT ON')
            # 'Run' keypress. Sets and enables for continuously initiated measurements.
        elif val == 'SINGLE':
            self._visainstrument.write(':INIT:CONT OFF')
            # 'Stop/Single' keypress. Initiates a single measurement and stop.

    def do_get_freq(self, channel):
#        if val == 'MEASURE':
#            return self._visainstrument.write(':MEAS:FREQ? 20e6,10 ,(@1)')
            # Configures instrument, initiates measurement, and queries for 
            # the result. Arming mode is automatically changed to 'DIGITS' 
            # by this command.
            # Automatically changes to ':INIT:CONT OFF' ('Stop/Single' key) 
            # after measurement.
        if channel == 'read':
            return self._visainstrument.ask(':READ:FREQUENCY?')
            # Automatically changes to ':INIT:CONT OFF' ('Stop/Single' key).
            # Initiates instrument and queries for the fresh result.
        elif channel == 'fetch':
            return self._visainstrument.ask('FETCH:FREQUENCY?')
            # Only queries for the result. Does not affect the ':INIT:CONT' state.
            # If ':INIT:CONT ON', queries for the fresh result after each 'FETCH' command.
            # If ':INIT:CONT OFF', only queries for the result of the latest initiated measurement.
            
#    def do_get_freq(self, channel):        

    def do_get_freq_ratio_1to2(self):
            self._visainstrument.write('FUNC "FREQ:RAT 1,2"')
            return self._visainstrument.ask('FETCH:FREQ:RAT?')

    def do_get_freq_ratio_2to1(self):
        self._visainstrument.write('FUNC "FREQ:RAT 2,1"')
        return self._visainstrument.ask('FETCH:FREQ:RAT?')

# The other measurement functions are not included.
 
# Gate & ExtArm key
    def do_set_arming(self, arm):
        if arm == 'AUTO':
            self._visainstrument.write('FREQ:ARM:SOUR IMM')
            self._visainstrument.write('FREQ:ARM:STOP:SOUR IMM')
        elif arm == 'DIGITS':
            self._visainstrument.write('FREQ:ARM:SOUR IMM')
            self._visainstrument.write('FREQ:ARM:STOP:SOUR DIG')
        elif arm == 'TIME':
            self._visainstrument.write('FREQ:ARM:SOUR IMM')
            self._visainstrument.write('FREQ:ARM:STOP:SOUR TIM')
        '''
        Default arming mode is 'TIME' after power up.
        External arming is not included in this driver.     
        '''

    def do_get_arming(self):
        val = self._visainstrument.ask('FREQ:ARM:STOP:SOUR?')
        if val == 'TIM':
            return 'time'
        elif val == 'IMM':
            return 'auto'
        elif val == 'DIG':
            return 'digits'

    def do_set_arming_digits(self, dig):
        self._visainstrument.write('FREQ:ARM:STOP:DIG ' + str(dig))

    def do_get_arming_digits(self):
        return self._visainstrument.ask('FREQ:ARM:STOP:DIG?')

    def do_set_arming_time(self, tim):
        self._visainstrument.write('FREQ:ARM:STOP:TIM ' + str(tim))
        '''
        Default gate time is 100 ms after power up.
        Resolution for short gate time (1e-3 to 99.99e-3 s): 0.01e-3 s
        Resolution for long gate time (100e-3 to 1000.000 s): 1e-3 s     
        '''

    def do_get_arming_time(self):
        return self._visainstrument.ask('FREQ:ARM:STOP:TIM?')

# Input channels conditioning keys
    # Trigger & Sensitivity
    def do_set_auto_trigger(self, on, channel):
        if on:
            self._visainstrument.write(':EVENT%s:LEVEL:AUTO ON' % channel)
        else:
            self._visainstrument.write(':EVENT%s:LEVEL:AUTO OFF' % channel)
        '''
        Input: 
            1 or True = on
            0 or False = off     
        '''

    def do_get_auto_trigger(self, channel):
        trigger_status = self._visainstrument.ask(':EVENT%s:LEVEL:AUTO?' % channel)
        if trigger_status == '1':
            return True
        elif trigger_status == '0':
            return False

    def do_set_trigger_level(self, level, channel):
        '''Set the trigger level for the specified channel'''
        trigger_status = self._visainstrument.ask(':EVENT%s:LEVEL:AUTO?' % channel)
        if trigger_status == '1':
            self._visainstrument.write(':EVENT' + str(channel) + ':LEV:REL ' + str(level))
            '''
            Range = 0 - 100        
            '''
        elif trigger_status== '0':
            self._visainstrument.write(':EVENT' + str(channel) + ':LEV ' + str(level))
            '''
            Range = -5.125V - +5.125V, minimum step 5 mV.      
            '''

    def do_get_trigger_level(self, channel):
        trigger_status = self._visainstrument.ask(':EVENT%s:LEVEL:AUTO?' % channel)
        if trigger_status == '1':
            return self._visainstrument.ask(':EVENT%s:LEV:REL?' % channel)
        elif trigger_status== '0':
            return self._visainstrument.ask(':EVENT%s:LEV?' % channel)

    def do_set_slope(self, val, channel):
        if val == 'POS':
            self._visainstrument.write(':EVENT%s:SLOPE POS' % channel)
        elif val == 'NEG':
            self._visainstrument.write(':EVENT%s:SLOPE NEG' % channel)

    def do_get_slope(self, channel):
        slope = self._visainstrument.ask(':EVENT%s:SLOPE?' % channel)
        if slope == 'POS':
            return 'pos'
        elif slope == 'NEG':
            return 'neg'

    def do_set_sensitivity(self, sens, channel):
        if sens == 'HI':
            self._visainstrument.write(':EVENT%s:HYST:REL 0' % channel)
        elif sens == 'MED':
            self._visainstrument.write(':EVENT%s:HYST:REL 50' % channel)
        elif sens == 'LOW':
            self._visainstrument.write(':EVENT%s:HYST:REL 100' % channel)

    def do_get_sensitivity(self, channel):
        sens = self._visainstrument.ask(':EVENT%s:HYST:REL?' % channel)
        if sens == '+0':
            return 'HI'
        elif sens == '+50':
            return 'MED'
        elif sens == '+100':
            return 'LOW'

        # Common 1 to be defined for TI 1 to 2

    # impedance
    def do_set_impedance(self, imp, channel):
        '''
        Input: 50, 1e6     
        '''
        self._visainstrument.write(':INP' + str(channel) + ':IMP ' + str(imp))
        
    def do_get_impedance(self, channel):
        return self._visainstrument.ask(':INP%s:IMP?' % channel)

    # DC/AC coupling
    def do_set_coupling(self, coup, channel):
        if coup == 'AC':
            self._visainstrument.write(':INP%s:COUP AC' % channel)
        elif coup == 'DC':
            self._visainstrument.write(':INP%s:COUP DC' % channel)

    def do_get_coupling(self, channel):
        return self._visainstrument.ask(':INP%s:COUP?' % channel)

    # attenuation
    def do_set_attenuation(self, att, channel):
        '''
        Input: 1, 10     
        '''
        self._visainstrument.write(':INP' + str(channel) + ':ATT ' + str(att))

    def do_get_attenuation(self, channel):
        '''Get the attenuation on the input'''
        return float(self._visainstrument.ask(':INP%s:ATT?' % channel))

    # 100kHz filter
    def do_set_filter(self, on, channel):
        if on:
            self._visainstrument.write(':INP%s:FILT ON' % channel)
        else:
            self._visainstrument.write(':INP%s:FILT OFF' % channel)

    def do_get_filter(self, channel):
        filter_status = self._visainstrument.ask(':INP%s:FILT?' % channel)
        if filter_status == '1':
            return True
        elif filter_status == '0':
            return False

# Limits keys (not available for Totalize and Voltage Peaks measurement)
    def do_set_upper_limit(self,val):
        self._visainstrument.write(':CALC2:LIM:UPP ' + str(val))

    def do_get_upper_limit(self):
        return self._visainstrument.ask(':CALC2:LIM:UPP?')

    def do_set_lower_limit(self,val):
        self._visainstrument.write(':CALC2:LIM:LOW ' + str(val))

    def do_get_lower_limit(self):
        return self._visainstrument.ask(':CALC2:LIM:LOW?')

    def do_set_limit_state(self,on):
        if on:
            self._visainstrument.write(':CALC2:LIM:STAT ON')
        else:
            self._visainstrument.write(':CALC2:LIM:STAT OFF')

    def do_get_limit_state(self):
        lim = self._visainstrument.ask(':CALC2:LIM:STAT?')
        if lim == '1':
            return True
        elif lim == '0':
            return False

    def do_set_on_fail(self,fail):
        answer = self._visainstrument.ask(':CALC2:LIM:STAT?')
        if answer == '0':
            logging.warning('Limit state is OFF. Turn ON to change ON FAIL state.')
        elif answer == '1':
            if fail == 'STOP':
                self._visainstrument.write('INIT:AUTO ON')
            elif fail == 'GO_ON':
                self._visainstrument.write('INIT:AUTO OFF')

    def do_get_on_fail(self):
        answer = self._visainstrument.ask(':CALC2:LIM:STAT?')
        if answer == '0':
            logging.warning('Limit state is OFF. Turn ON to enable ON FAIL function.')
            fail = self._visainstrument.ask('INIT:AUTO?')
            if fail == '1':
                return 'stop'
            else:
                return 'go_on'
        else:
            fail = self._visainstrument.ask('INIT:AUTO?')
            if fail == '1':
                return 'stop'
            else:
                return 'go_on'

    def do_set_limit_display(self,dis):
        if dis == 'NUMBER':
            self._visainstrument.write(':CALC2:LIM:DISP NUMB')
        elif dis == 'GRAPH':
            self._visainstrument.write(':CALC2:LIM:DISP GRAP')

    def do_get_limit_display(self):
        return self._visainstrument.ask(':CALC2:LIM:DISP?')

# Math keys
    def do_set_stats_display(self,stats):
        if stats == 'MAX':
            self._visainstrument.write(':DISP:TEXT:FEED "CALC3"')
            self._visainstrument.write(':CALC3:AVER:TYPE MAX')
        elif stats == 'MIN':
            self._visainstrument.write(':DISP:TEXT:FEED "CALC3"')
            self._visainstrument.write(':CALC3:AVER:TYPE MIN')
        elif stats == 'STD_DEV':
            self._visainstrument.write(':DISP:TEXT:FEED "CALC3"')
            self._visainstrument.write(':CALC3:AVER:TYPE SDEV')
        elif stats == 'MEAN':
            self._visainstrument.write(':DISP:TEXT:FEED "CALC3"')
            self._visainstrument.write(':CALC3:AVER:TYPE MEAN')
        elif stats == 'MEAS':
            self._visainstrument.write(':DISP:TEXT:FEED "CALC2"')

    def do_get_stats_display(self):
        stats = self._visainstrument.ask(':DISP:TEXT:FEED?')
        if stats == '"CALC2"':
            return 'MEAS'
        else:
            return self._visainstrument.ask(':CALC3:AVER:TYPE?')

    def do_set_stats_count(self,val):
        self._visainstrument.write(':CALC3:AVER:COUN ' + str(val))

    def do_get_stats_count(self):
        return self._visainstrument.ask(':CALC3:AVER:COUN?')

    def do_set_stats_state(self,val):
        if val:
            self._visainstrument.write(':CALC3:AVER ON')
        else:
            self._visainstrument.write(':CALC3:AVER OFF')

    def do_get_stats_state(self):
        val = self._visainstrument.ask(':CALC3:AVER?')
        if val == '1':
            return True
        elif val == '0':
            return False

    def do_set_stats_use(self,val):
        if val == 'ALL_MEAS':
            self._visainstrument.write(':CALC3:LFIL:STAT OFF')
        elif val == 'IN_LIMIT':
            self._visainstrument.write(':CALC3:LFIL:STAT ON')
            # Limit Testing and Stats functions are independent.
            # LIM TEST: doesn't have to be ON in order to filter measurements 
            # for statistics.     

    def do_get_stats_use(self):
        val = self._visainstrument.ask(':CALC3:LFIL:STAT?')
        if val == '1':
            return 'in_limit'
        elif val == '0':
            return 'all_meas'

    def do_set_stats_on_single(self,val):
        if val == '1':
            self._visainstrument.write(':TRIG:COUN:AUTO OFF')
        elif val == 'N':
            self._visainstrument.write(':TRIG:COUN:AUTO ON')

    def do_get_stats_on_single(self):
        val = self._visainstrument.ask(':TRIG:COUN:AUTO?')
        if val == '1':
            return 'N'
        elif val == '0':
            return '1'
        '''
        1 or N measurements are taken by each 'Stop/Single' keypress or ':INIT[:IMM]' command.     
        '''

    def do_set_scale(self,val):
        self._visainstrument.write(':TRAC SCALE, ' + str(val))

    def do_get_scale(self):
        return self._visainstrument.ask(':TRAC? SCALE')

    def do_set_offset(self,val):
        self._visainstrument.write(':TRAC OFFSET, ' + str(val))

    def do_get_offset(self):
        return self._visainstrument.ask(':TRAC? OFFSET')

    def do_set_math_state(self,val):
        if val:
            self._visainstrument.write(':CALC:MATH:STAT ON')
        else:
            self._visainstrument.write(':CALC:MATH:STAT OFF')

    def do_get_math_state(self):
        val = self._visainstrument.ask(':CALC:MATH:STAT?')
        if val == '1':
            return True
        elif val == '0':
            return False

    def do_get_timebase(self):
        '''Queries whether the internal or external timebase is used'''
        response = self._visainstrument.ask(':SENS:ROSC:SOUR?')
        return response

    def get_last_error_message(self):
        return self._visainstrument.ask(':SYST:ERR?')
    
