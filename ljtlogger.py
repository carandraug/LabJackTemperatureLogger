#!/usr/bin/env python

import re

import u6

import daqlog
from ktypeExample import mVoltsToTempC, tempCToMVolts

# Logging rate / ms
LOGRATE = 10000
# AIN1 screw terminal is physically closest to internal T-sensor.
CHANNEL = 1
# Cold junction offset measured with thermapen: T_measured - T_internal.
CJOFFSET = 1.4
# Kelvin to DegC offset.
KCOFFSET = 273.15

class DaqU6(object):
    def __init__(self):
        self.d = None
        self._connect()

    def _connect(self):
        if self.d:
            try:
                self.d.close()
            except:
                pass
        del(self.d)
        self.d = u6.U6()
        self.d.getCalibrationData()

    def readTemperature(self):
        try:
            temperature = self._readTemperature()
        except:
            self._connect()
            temperature = self._readTemperature()
        return temperature

    def _readTemperature(self):
        d = self.d
        # Cold junction in degC, with sensor-terminal offset compensation.
        coldJunc_C = d.getTemperature() + CJOFFSET - KCOFFSET
        # Cold junction im mV (from inverse k-type polynomial).
        coldJunc_mV = tempCToMVolts(coldJunc_C)
        # Remote junction mV.
        couple_mV = d.getAIN(CHANNEL, resolutionIndex=8, gainIndex=3) * 1000.
        # Cold junction + remote junction mV.
        total_mV = coldJunc_mV + couple_mV
        # Return 0-referenced temperature (from k-type polynomial).
        return mVoltsToTempC(total_mV)


def test():
    # Logger
    logger = daqlog.DataHandler()
    logger.start()
    # Data source
    source = DaqU6()
    # Acquirer
    daq = daqlog.Acquirer(LOGRATE/1000., source.readTemperature, logger.addToQueue)
    daq.start()
    return (daq, logger, plotterLong, plotterShort)


def main():
    # Logger
    logger = daqlog.DataHandler()
    logger.start()
    # Data source
    source = DaqU6()
    # Acquirer
    daq = daqlog.Acquirer(LOGRATE/1000., source.readTemperature, logger.addToQueue)
    daq.start()

    while 1:
        time.sleep(1)

    logger.stopAndJoin()
    daq.stopAndJoin()

if __name__ == '__main__':
    main()
