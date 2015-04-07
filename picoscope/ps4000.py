# This is the instrument-specific file for the PS3000a series of instruments.
#
# pico-python is Copyright (c) 2013-2014 By:
# Colin O'Flynn <coflynn@newae.com>
# Mark Harfouche <mark.harfouche@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
This is the low level driver file for a specific Picoscope.

By this, I mean if parameters want to get passed as strings, they should be
handled by PSBase
All functions here should take things as close to integers as possible, the
only exception here is for array parameters. Array parameters should be passed
in a pythonic way through numpy since the PSBase class should not be aware of
the specifics behind how the clib is called.

The functions should not have any default values as these should be handled
by PSBase.
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import math

# to load the proper dll
import platform

# Do not import or use ill definied data types
# such as short int or long
# use the values specified in the h file
# float is always defined as 32 bits
# double is defined as 64 bits
from ctypes import byref, POINTER, create_string_buffer, c_float, \
    c_int16, c_int32, c_uint16, c_uint32, c_void_p
from ctypes import c_int32 as c_enum

from picobase import _PicoscopeBase


class PS4000(_PicoscopeBase):
    """The following are low-level functions for the PS3000a"""

    LIBNAME = "ps4000"

    NUM_CHANNELS = 4
    CHANNELS     =  {"A": 0, "B": 1, "C": 2, "D": 3,
                     "External": 4, "MaxChannels": 4, "TriggerAux": 5,
                     "MaxTriggerSources": 6}

    ADC_RESOLUTIONS = {"8":0, "12":1, "14":2, "15":3, "16":4};

    CHANNEL_RANGE = [{"rangeV":10E-3, "apivalue":0, "rangeStr":"10 mV"},
                     {"rangeV":20E-3, "apivalue":1, "rangeStr":"20 mV"},
                     {"rangeV":50E-3, "apivalue":2, "rangeStr":"50 mV"},
                     {"rangeV":100E-3, "apivalue":3, "rangeStr":"100 mV"},
                     {"rangeV":200E-3, "apivalue":4, "rangeStr":"200 mV"},
                     {"rangeV":500E-3, "apivalue":5, "rangeStr":"500 mV"},
                     {"rangeV":1.0, "apivalue":6, "rangeStr":"1 V"},
                     {"rangeV":2.0, "apivalue":7, "rangeStr":"2 V"},
                     {"rangeV":5.0, "apivalue":8, "rangeStr":"5 V"},
                     {"rangeV":10.0, "apivalue":9, "rangeStr":"10 V"},
                     {"rangeV":20.0, "apivalue":10, "rangeStr":"20 V"},
                     {"rangeV":50.0, "apivalue":11, "rangeStr":"50 V"},
                     {"rangeV":100.0, "apivalue":12, "rangeStr":"100 V"},
                     ]

    CHANNEL_COUPLINGS = {"DC":1, "AC":0}


    MAX_VALUE_8BIT = 32512
    MIN_VALUE_8BIT = -32512
    MAX_VALUE_OTHER = 32767
    MIN_VALUE_OTHER = -32767

    EXT_RANGE_VOLTS = 5

    def __init__(self, serialNumber=None, connect=True):
        """Load DLL etc"""
        if platform.system() == 'Linux':
            from ctypes import cdll
            self.lib = cdll.LoadLibrary("lib" + self.LIBNAME + ".so")
        else:
            from ctypes import windll
            self.lib = windll.LoadLibrary(self.LIBNAME + ".dll")

        self.resolution = self.ADC_RESOLUTIONS["8"]

        super(PS4000, self).__init__(serialNumber, connect)

    def _lowLevelOpenUnit(self, sn):
        c_handle = c_int16()
        if sn is not None:
            serialNullTermStr = create_string_buffer(sn)
        else:
            serialNullTermStr = None
        # Passing None is the same as passing NULL
        m = self.lib.ps4000OpenUnitEx(byref(c_handle), byref(serialNullTermStr))
        self.checkResult(m)
        self.handle = c_handle.value

    def _lowLevelCloseUnit(self):
        m = self.lib.ps4000CloseUnit(c_int16(self.handle))
        self.checkResult(m)

    def _lowLevelSetChannel(self, chNum, enabled, coupling, VRange, VOffset,
                            BWLimited):
        m = self.lib.ps4000SetChannel(c_int16(self.handle), c_enum(chNum),
                                      c_int16(enabled), c_enum(coupling),
                                      c_enum(VRange))
        self.checkResult(m)

    def _lowLevelStop(self):
        m = self.lib.ps4000Stop(c_int16(self.handle))
        self.checkResult(m)

    def _lowLevelGetUnitInfo(self, info):
        s = create_string_buffer(256)
        requiredSize = c_int16(0)

        m = self.lib.ps4000GetUnitInfo(c_int16(self.handle), byref(s),
                                       c_int16(len(s)), byref(requiredSize),
                                       c_enum(info))
        self.checkResult(m)
        if requiredSize.value > len(s):
            s = create_string_buffer(requiredSize.value + 1)
            m = self.lib.ps4000GetUnitInfo(c_int16(self.handle), byref(s),
                                           c_int16(len(s)),
                                           byref(requiredSize), c_enum(info))
            self.checkResult(m)

        # should this bee ascii instead?
        # I think they are equivalent...
        return s.value.decode('utf-8')

    def _lowLevelFlashLed(self, times):
        m = self.lib.ps4000FlashLed(c_int16(self.handle), c_int16(times))
        self.checkResult(m)

    def _lowLevelSetSimpleTrigger(self, enabled, trigsrc, threshold_adc,
                                  direction, delay, auto):
        m = self.lib.ps4000SetSimpleTrigger(
            c_int16(self.handle), c_int16(enabled),
            c_enum(trigsrc), c_int16(threshold_adc),
            c_enum(direction), c_uint32(delay), c_int16(auto))
        self.checkResult(m)

    def _lowLevelSetNoOfCaptures(self, numCaptures):
        m = self.lib.ps4000SetNoOfCaptures(c_int16(self.handle),
            c_uint16(numCaptures))
        self.checkResult(m)

    def _lowLevelMemorySegments(self, numSegments):
        maxSamples = c_int32()
        m = self.lib.ps4000MemorySegments(c_int16(self.handle),
            c_uint16(numSegments), byref(maxSamples))
        self.checkResult(m)
        return maxSamples.value

    def _lowLevelGetMaxSegments(self):
        throw Exception("No ps4000GetMaxSegments function exists")

    def _lowLevelRunBlock(self, numPreTrigSamples, numPostTrigSamples,
                          timebase, oversample, segmentIndex):
        #NOT: Oversample is NOT used!
        timeIndisposedMs = c_int32()
        m = self.lib.ps4000RunBlock(
            c_int16(self.handle), c_uint32(numPreTrigSamples),
            c_uint32(numPostTrigSamples), c_uint32(timebase),
            c_int16(oversample), byref(timeIndisposedMs), c_uint16(segmentIndex),
            c_void_p(), c_void_p())
        self.checkResult(m)
        return timeIndisposedMs.value

    def _lowLevelIsReady(self):
        ready = c_int16()
        m = self.lib.ps4000IsReady(c_int16(self.handle), byref(ready))
        self.checkResult(m)
        if ready.value:
            return True
        else:
            return False

    def _lowLevelGetTimebase(self, tb, noSamples, oversample, segmentIndex):
        """ returns (timeIntervalSeconds, maxSamples) """
        maxSamples = c_int32()
        intervalNanoSec = c_float()

        m = self.lib.ps4000GetTimebase2(c_int16(self.handle), c_uint32(tb),
                                        c_uint32(noSamples), byref(intervalNanoSec),
                                        c_int16(oversample), byref(maxSamples),
                                        c_uint32(segmentIndex))
        self.checkResult(m)
        # divide by 1e9 to return interval in seconds
        return (intervalNanoSec.value * 1e-9, maxSamples.value)

    def getTimeBaseNum(self, sampleTimeS):
        """
        Convert sample time in S to something to pass to API Call
        """
        maxSampleTime = (((2 ** 32 - 1) - 2) / 125000000)
        if sampleTimeS < 8.0E-9:
            st = math.floor(math.log(sampleTimeS * 1E9, 2))
            st = max(st, 0)
        else:
            if sampleTimeS > maxSampleTime:
                sampleTimeS = maxSampleTime
            st = math.floor((sampleTimeS * 125000000) + 2)

        # is this cast needed?
        st = int(st)
        return st

    def getTimestepFromTimebase(self, timebase):
        '''
        Takes API timestep code (an integer from 0-32) and returns
        the sampling interval it indicates, in seconds.
        '''
        if timebase < 3:
            dt = 2. ** timebase / 1.0E9
        else:
            dt = (timebase - 2.0) / 125000000.
        return dt


    def _lowLevelSetDataBuffer(self, channel, data, downSampleMode, segmentIndex):
        """
        data should be a numpy array

        Be sure to call _lowLevelClearDataBuffer
        when you are done with the data array
        or else subsequent calls to GetValue will still use the same array.
        """
        dataPtr = data.ctypes.data_as(POINTER(c_int16))
        numSamples = len(data)

        m = self.lib.ps4000SetDataBuffer(c_int16(self.handle), c_enum(channel),
                                         dataPtr, c_int32(numSamples))
        self.checkResult(m)


    def _lowLevelClearDataBuffer(self, channel, segmentIndex):
        """ data should be a numpy array"""
        m = self.lib.ps4000SetDataBuffer(c_int16(self.handle), c_enum(channel),
                                         c_void_p(), c_uint32(0))
        self.checkResult(m)

    def _lowLevelGetValues(self, numSamples, startIndex, downSampleRatio,
                           downSampleMode, segmentIndex):
        numSamplesReturned = c_uint32()
        numSamplesReturned.value = numSamples
        overflow = c_int16()
        m = self.lib.ps4000GetValues(
            c_int16(self.handle), c_uint32(startIndex),
            byref(numSamplesReturned), c_uint32(downSampleRatio),
            c_enum(downSampleMode), c_uint32(segmentIndex),
            byref(overflow))
        self.checkResult(m)
        return (numSamplesReturned.value, overflow.value)

    def _lowLevelGetValuesBulk(self, numSamples, fromSegment, toSegment,
        downSampleRatio, downSampleMode, overflow):

        m = self.lib.ps4000GetValuesBulk(c_int16(self.handle),
            byref(c_int16(numSamples)),
            c_int16(fromSegment),
            c_int16(toSegment),
            overflow.ctypes.data_as(POINTER(c_int16))
            )
        self.checkResult(m)
        return overflow, numSamples

    # def _lowLevelSetSigGenBuiltInSimple(self, offsetVoltage, pkToPk, waveType,
    #                                     frequency, shots, triggerType,
    #                                     triggerSource):
    #     # TODO, I just noticed that V2 exists
    #     # Maybe change to V2 in the future
    #     m = self.lib.ps3000SetSigGenBuiltIn(
    #         c_int16(self.handle),
    #         c_int32(int(offsetVoltage * 1000000)),
    #         c_int32(int(pkToPk        * 1000000)),
    #         c_int16(waveType),
    #         c_float(frequency), c_float(frequency),
    #         c_float(0), c_float(0), c_enum(0), c_enum(0),
    #         c_uint32(shots), c_uint32(0),
    #         c_enum(triggerType), c_enum(triggerSource),
    #         c_int16(0))
    #     self.checkResult(m)
