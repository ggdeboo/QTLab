# labbrick.py, python wrapper for Lab Brick DLL
# Gabriele de Boo <ggdeboo@gmail.com>, 2014
#

import os
import ctypes

DEVID = ctypes.c_uint
LVSTATUS = ctypes.c_uint

if os.name == "posix":
    LMShid = ctypes.cdll.LoadLibrary("/home/giuseppe1/Downloads/Vaunix/vnx_LMS_API/LMS Linux SDK/LMS090/LMShid.o")
    linux = True
elif os.name == "nt":
    LMShid = ctypes.cdll.vnx_fmsynth
    linux = False 
else:
    print 'Operating system not supported'

if linux:
    fnLMS_perror = LMShid.fnLMS_perror
    fnLMS_perror.restype = ctypes.c_char_p
GetFrequency = LMShid.fnLMS_GetFrequency
GetFrequency.restype = LVSTATUS

INVALID_DEVID = 0x80000000
DEVICE_NOT_READY = 0x80030000

def status_chk(status):
    '''Get the status description from the library.'''
    if status != 0:
	if linux:
            error_msg = fnLMS_perror(LVSTATUS(status))
            raise RuntimeError('labbrick call failed with error %d: %s' % \
                (status, error_msg))
        else:
            raise RuntimeError('labbrick call failed with error: %s' % status)

def error_chk(retvalue):
    '''For the functions that return either a value or an error.'''
    if retvalue == DEVICE_NOT_READY:
        raise RuntimeError('labbrick call failed: Device not ready.')
    elif retvalue == INVALID_DEVID:
        raise RuntimeError('labbrick call failed: Invalid device id.')
    return retvalue
    
def init():
    '''Initialize the library.'''
    if linux:
        LMShid.fnLMS_Init()

def set_testmode(mode=False):
    '''Set whether the library is running in test mode or not.'''
    LMShid.fnLMS_SetTestMode(ctypes.c_bool(mode))

def get_numdevices():
    '''Get the number of connected devices.'''
    n = LMShid.fnLMS_GetNumDevices()
    return n

def get_activedevices():
    '''
    Fill the activeDevices array with the active devices. 
    Returns a list of the active devices DEVID numbers.
    '''
    activeDevicesArray = (DEVID * 64)()
    p = ctypes.cast(activeDevicesArray, ctypes.POINTER(ctypes.c_uint))
    activeDevicescount = LMShid.fnLMS_GetDevInfo(p)
    activeDevicesList = []
    for devices in range(activeDevicescount):
        activeDevicesList.append(activeDevicesArray[devices])
    return activeDevicesList

def get_modelname(device):
    '''Get the modelname for nth device.'''
    modelname = (ctypes.c_char * 32)()
    p = ctypes.cast(modelname, ctypes.POINTER(ctypes.c_char))
    nchars = LMShid.fnLMS_GetModelName(DEVID(device), p)
    return modelname[:nchars]

def init_device(device):
    '''Initialize the nth device. Return the status.'''
    status_chk(LMShid.fnLMS_InitDevice(DEVID(device)))

def get_frequency(device):
    '''Get the frequency of the nth device.'''
    return int(error_chk(GetFrequency(DEVID(device))))

def set_frequency(device, freq):
    '''Set the frequency of the nth device. In steps of 10 Hz.'''
    status_chk(LMShid.fnLMS_SetFrequency(DEVID(device), ctypes.c_int(freq)))   
    
def get_start_frequency(device):
    '''Get the start frequency of the nth device.'''
    return int(error_chk(LMShid.fnLMS_GetStartFrequency(DEVID(device))))

def set_start_frequency(device, freq):
    '''Set the start frequency of the nth device.'''
    status_chk(LMShid.fnLMS_SetStartFrequency(DEVID(device)))

def get_end_frequency(device):
    '''Get the end frequency of the nth device.'''
    return int(error_chk(LMShid.fnLMS_GetEndFrequency(DEVID(device))))

def get_serial_number(device):
    '''Get the serial number of the nth device.'''
    return int(LMShid.fnLMS_GetSerialNumber(DEVID(device)))

def get_rf_on(device):
    '''Get the status of the RF output of the nth device.'''
    return bool(LMShid.fnLMS_GetRF_On(DEVID(device)))

def set_rf_on(device, on):
    '''Set the status of the RF output of the nth device to the value given by on (True or False).'''
    status_chk(LMShid.fnLMS_SetRFOn(DEVID(device), ctypes.c_bool(on)))

def get_use_internal_ref(device):
    '''Get whether the instrument is using the internal reference or not.'''
    return bool(error_chk(LMShid.fnLMS_GetUseInternalRef(DEVID(device))))

def set_use_internal_ref(device, internal):
    '''Set whether the instrument uses the internal reference or not.'''
    status_chk(LMShid.fnLMS_SetUseInternalRef(DEVID(device), ctypes.c_bool(internal)))

def get_power_level(device):
    '''
    Get the power level of the device.
    Integer number of .25 dB units.
    According to the specifications the library should return the power level, but it seems like it returns the attenuation amount. A conversion is made in the function.
    '''
    maxpower = get_max_power(device)
    return (maxpower - int(error_chk(LMShid.fnLMS_GetPowerLevel(DEVID(device)))))

def set_power_level(device, powerlevel):
    '''
    Set the power level to the value given by powerlevel.
    The power level is specified in .25 dB units. 
    The encoding is: powerlevel = desired output power in dBm / .25 dB
    '''
    status_chk(LMShid.fnLMS_SetPowerLevel(DEVID(device), ctypes.c_int(powerlevel)))

def get_min_power(device):
    '''Get the minimal settable power.'''
    return int(error_chk(LMShid.fnLMS_GetMinPwr(DEVID(device))))

def get_max_power(device):
    '''Get the maximal settable power.'''
    return int(error_chk(LMShid.fnLMS_GetMaxPwr(DEVID(device))))

def get_min_frequency(device):
    '''
    Get the minimal settable frequency.
    In steps of 10 Hz.
    '''
    return int(error_chk(LMShid.fnLMS_GetMinFreq(DEVID(device))))

def get_max_frequency(device):
    '''
    Get the maximal settable frequency.
    In steps of 10 Hz.
    '''
    return int(error_chk(LMShid.fnLMS_GetMaxFreq(DEVID(device))))

def get_sweep_time(device):
    '''Get the sweep time.'''
    return int(error_chk(LMShid.fnLMS_GetSweepTime(DEVID(device))))

def set_sweep_time(device, sweeptime):
    '''
    Set the sweep time.
    Units is millisecond (ms)
    '''
    status_chk(LMShid.fnLMS_SetSweepTime(DEVID(device), ctypes.c_int(sweeptime)))

def set_sweep_direction(device, up):
    '''
    Set the sweep direction.
    up : True
    down : False
    '''
    status_chk(LMShid.fnLMS_SetSweepDirection(DEVID(device), ctypes.c_bool(up)))
    
def set_sweep_mode(device, mode):
    '''
    Set the sweep mode. If mode = True the sweep will be repeated, if mode = False the sweep will only happen once.
    '''
    status_chk(LMShid.fnLMS_SetSweepMode(DEVID(device), ctypes.c_bool(mode)))

def set_sweep_type(device, swptype):
    '''
    Set the sweep time. If swptype = True then the sweep will be bidirectional, if swptype = False the sweep will only go in one direction.
    '''
    status_chk(LMShid.fnLMS_SetSweepType(DEVID(device), ctypes.c_bool(swtype)))

def start_sweep(device, go):
    '''
    Start a sweep. If go = True it starts sweeping, if go = False the sweep is stopped.
    '''
    status_chk(LMShid.fnLMS_StartSweep(DEVID(device), ctypes.c_bool(go)))

def save_settings(device):
    '''
    Save the current settings to the instrument.
    '''
    status_chk(LMShid.fnLMS_SaveSettings(DEVID(device)))

def close_device(device):
    '''
    Close the device interface to the synthesizer.
    '''
    status_chk(LMShid.fnLMS_CloseDevice(DEVID(device)))
