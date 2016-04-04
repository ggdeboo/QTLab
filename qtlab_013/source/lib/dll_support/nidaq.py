# nidaq.py, python wrapper for NIDAQ DLL
# Reinier Heeres <reinier@heeres.eu>, 2008
# Gabriele de Boo <ggdeboo@gmail.com>, 2015
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

import ctypes
import types
import numpy
import logging
import time
import os

if os.name == 'nt':
    nidaq = ctypes.windll.nicaiu
elif os.name == 'posix':
    nidaq = ctypes.cdll.LoadLibrary("libnidaqmx.so")
else:
    print 'Operating system not supported.'

int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32

DAQmx_Val_Cfg_Default = int32(-1)

DAQmx_Val_RSE               = 10083
DAQmx_Val_NRSE              = 10078
DAQmx_Val_Diff              = 10106
DAQmx_Val_PseudoDiff        = 12529

_config_map = {
    'DEFAULT': DAQmx_Val_Cfg_Default,
    'RSE': DAQmx_Val_RSE,
    'NRSE': DAQmx_Val_NRSE,
    'DIFF': DAQmx_Val_Diff,
    'PSEUDODIFF': DAQmx_Val_PseudoDiff,
}

DAQmx_Val_Volts             = 10348
DAQmx_Val_Rising            = 10280
DAQmx_Val_Falling           = 10171
DAQmx_Val_FiniteSamps       = 10178
DAQmx_Val_GroupByChannel    = 0
DAQmx_Val_GroupByScanNumber = 1

DAQmx_Val_CountUp           = 10128
DAQmx_Val_CountDown         = 10124
DAQmx_Val_ExtControlled     = 10326

def CHK(err):
    '''Error checking routine'''

    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
        raise RuntimeError('Nidaq call failed with error %d: %s' % \
            (err, repr(buf.value)))

def buf_to_list(buf):
    name = ''
    namelist = []
    for ch in buf:
        if ch in '\000 \t\n':
            name = name.rstrip(',')
            if len(name) > 0:
                namelist.append(name)
                name = ''
            if ch == '\000':
                break
        else:
            name += ch

    return namelist

def get_device_names():
    '''Return a list of available NIDAQ devices.'''
    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetSysDevNames(ctypes.byref(buf), bufsize)
    return buf_to_list(buf)[0]

def get_device_type(dev):
    '''Get the type of a DAQ device.'''
    # int32 __CFUNC DAQmxGetDevProductType(const char device[], char *data,
    # uInt32 bufferSize)
    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevProductType(dev, ctypes.byref(buf), bufsize) 
    return buf_to_list(buf)[0]

def get_input_voltage_ranges(dev):
    '''Get the available voltage ranges for the AI connected DAQ.'''
    bufsize = 32
    range_list_type = float64 * bufsize
    range_list = range_list_type()
    nidaq.DAQmxGetDevAIVoltageRngs(dev, ctypes.byref(range_list), uInt32(bufsize))
    range_list = list(range_list)
    range_values_n = range_list.index(0.0)
    range_n = range_values_n / 2
    return_list = []
    for idx in range(range_n):
        return_list.append([range_list[2*idx],
                            range_list[(2*idx)+1]])        
    return return_list

def get_output_voltage_ranges(dev):
    '''Get the available voltage ranges for the AO connected DAQ.'''
    bufsize = 32
    range_list_type = float64 * bufsize
    range_list = range_list_type()
    nidaq.DAQmxGetDevAOVoltageRngs(dev, ctypes.byref(range_list), uInt32(bufsize))
    range_list = list(range_list)
    range_values_n = range_list.index(0.0)
    range_n = range_values_n / 2
    return_list = []
    for idx in range(range_n):
        return_list.append([range_list[2*idx],
                            range_list[(2*idx)+1]])        
    return return_list

def get_maximum_input_channel_rate(dev):
    '''Get the highest sample rate for a single input channel'''
    sample_rate = float64()
    nidaq.DAQmxGetDevAIMaxSingleChanRate(dev, ctypes.byref(sample_rate))
    return sample_rate.value    

def get_minimum_input_channel_rate(dev):
    '''Get the minimum sample rate an input channel'''
    sample_rate = float64()
    nidaq.DAQmxGetDevAIMinRate(dev, ctypes.byref(sample_rate))
    return sample_rate.value    

def get_maximum_output_channel_rate(dev):
    '''Get the maximum update rate for an output channel'''
    sample_rate = float64()
    nidaq.DAQmxGetDevAOMaxRate(dev, ctypes.byref(sample_rate))
    return sample_rate.value

def get_simultaneous_sampling_support(dev):
    '''Get whether simultaneous sampling is supported'''
    sim_sampling = ctypes.c_bool()
    nidaq.DAQmxGetDevAISimultaneousSamplingSupported(dev,
                                                ctypes.byref(sim_sampling))
    return sim_sampling.value

def reset_device(dev):
    '''Reset device "dev"'''
    nidaq.DAQmxResetDevice(dev)

def get_physical_input_channels(dev):
    '''Return a list of physical input channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAIPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_output_channels(dev):
    '''Return a list of physical output channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAOPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_counter_channels(dev):
    '''Return a list of physical counter channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevCIPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def read(devchan, samples=1, freq=10000.0, minv=-10.0, maxv=10.0,
            timeout=10.0, config=DAQmx_Val_Cfg_Default, 
            averaging=True, triggered = False,
            trigger_slope='POS',
            pre_trig_samples=0):
    '''
    Read up to max_samples from a channel. Seems to have trouble reading
    1 sample!

    Input:
        devchan (string): device/channel specifier, such as Dev1/ai0
        samples (int): the number of samples to read
        freq (float): the sampling frequency
        minv (float): the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion
        config (string or int): the configuration of the channel
        triggered (boolean): whether the measurement is triggered
        trigger_slope (string): whether we are using the positive or negative
                                slope for the trigger.
        
    Output:
        A numpy.array with the data on success, None on error

    '''
    timeout = timeout + samples/freq

    if type(config) is types.StringType:
        if config in _config_map:
            config = _config_map[config]
        else:
            return None
    if type(config) is not types.IntType:
        return None
    
    if samples == 1:
        retsamples = 1
        samples = 2
    else:
        retsamples = samples

    data = numpy.zeros(samples, dtype=numpy.float64)

    taskHandle = TaskHandle(0)
    read = int32()
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle, devchan, "",
            config,
            float64(minv), float64(maxv),
            DAQmx_Val_Volts, None))

        if retsamples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                uInt64(samples)));
            
            if triggered:
                if trigger_slope == 'POS':
                    slope = DAQmx_Val_Rising
                elif trigger_slope == 'NEG':
                    slope = DAQmx_Val_Falling
                else:
                    raise ValueError('Use POS or NEG for the trigger slope')
	        CHK(nidaq.DAQmxCfgDigEdgeRefTrig(taskHandle,
                                "/Dev1/PFI0",slope,
                                uInt32(pre_trig_samples)));
                
            CHK(nidaq.DAQmxStartTask(taskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(taskHandle, samples, float64(timeout),
                DAQmx_Val_GroupByChannel, data.ctypes.data,
                samples, ctypes.byref(read), None))
        else:
            CHK(nidaq.DAQmxReadAnalogScalarF64(taskHandle, float64(timeout),
                data.ctypes.data, None))
            read = int32(1)

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))
    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    if read > 0:
        if retsamples == 1:
            return data[0]
        else:
            #Jan added numpy.mean()
            if averaging:
                return numpy.mean(data)# Max added list() and removed numpy.mean()
            else:
                return data
            #return list(data[:read.value])
    else:
        return None

def write(devchan, data, freq=10000.0, minv=-10.0, maxv=10.0,
                timeout=10.0):
    '''
    Write values to channel

    Input:
        devchan (string): device/channel specifier, such as Dev1/ao0
        data (int/float/numpy.array): data to write
        freq (float): the update rate
        minv (float): the maximum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion

    Output:
        Number of values written
    '''

    if type(data) in (types.IntType, types.FloatType):
        data = numpy.array([data], dtype=numpy.float64)
    elif isinstance(data, numpy.ndarray):
        if data.dtype is not numpy.float64:
            data = numpy.array(data, dtype=numpy.float64)
    elif len(data) > 0:
        data = numpy.array(data, dtype=numpy.float64)
    samples = len(data)

    taskHandle = TaskHandle(0)
    written = int32()
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateAOVoltageChan(taskHandle, devchan, "",
            float64(minv), float64(maxv), DAQmx_Val_Volts, None))

        if len(data) == 1:
            CHK(nidaq.DAQmxWriteAnalogScalarF64(taskHandle, 1, float64(timeout),
                float64(data[0]), None))
            written = int32(1)
        else:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(samples)))
            CHK(nidaq.DAQmxWriteAnalogF64(taskHandle, samples, 0, float64(timeout),
                DAQmx_Val_GroupByChannel, data.ctypes.data,
                ctypes.byref(written), None))
            CHK(nidaq.DAQmxStartTask(taskHandle))
    except Exception, e:
        logging.error('NI DAQ call failed (correct channel configuration ' + 
                        'selected?): %s', str(e))
    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)
    return written.value


def read_counter(devchan="/Dev1/ctr0", samples=1, freq=1.0, timeout=1.0, src=""):
    '''
    Read counter 'devchan'.
    Specify source pin with 'src'.
    '''

    taskHandle = TaskHandle(0)
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        initial_count = int32(0)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(taskHandle, devchan, "",
                DAQmx_Val_Rising, initial_count, DAQmx_Val_CountUp))
        if src is not None and src != "":
            CHK(nidaq.DAQmxSetCICountEdgesTerm(taskHandle, devchan, src))

        nread = int32()
        data = numpy.zeros(samples, dtype=numpy.float64)
        if samples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                uInt64(samples)));
            CHK(nidaq.DAQmxStartTask(taskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(taskHandle, int32(samples), float64(timeout),
               DAQmx_Val_GroupByChannel, data.ctypes.data,
               samples, ctypes.byref(read), None))
        else:
            CHK(nidaq.DAQmxStartTask(taskHandle))
            time.sleep(1.0 / freq)
            nread = int32(0)
            CHK(nidaq.DAQmxReadCounterF64(taskHandle, int32(samples), float64(timeout),
                data.ctypes.data, int32(samples), ctypes.byref(nread), None))
            nread = int32(1)

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))

    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    if nread.value == 1:
        return int(data[0])
    else:
        return data

