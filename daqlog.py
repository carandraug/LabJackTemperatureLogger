#!/usr/bin/env python

from collections import deque, Container
import io
import threading
import time
import os

class StartStopThread(threading.Thread):
    def __init__(self):
        super(StartStopThread, self).__init__()
        self.runFlag = None

    def start(self):
        self.runFlag = True
        super(StartStopThread, self).start()

    def stopAndJoin(self):
        self.runFlag = False
        self.join()


class DataHandler(StartStopThread):
    def __init__(self, headings=None, cols=2, filenameStr='%Y%m%d-%H%M%S.txt',
                 max_log_size=10000):
        super(DataHandler, self).__init__()
        # Run flag.
        # self.runFlag = None
        # Settings for output file.
        self.fileSettings = {'headings':headings,
                          'filenameStr': filenameStr,}
        # Number of columns.
        self.nCols = cols
        # max numer of lines in the log file before rotating
        self.max_log_size = max_log_size
        # Queue for incoming data.
        self.queue = deque()
        # Lock on queue.
        self.lock = threading.Lock()

    def addToQueue(self, *data):
        """Add a point to the queue."""
        with self.lock:
            self.queue.append(data)

    def run(self):
        """DataHandler main loop."""
        # Clear stale data from the queue.
        self.queue.clear()

        # Number of columns.
        nCols = self.nCols
        # Data format string.
        formatStr = self.fileSettings.get('formatStr')
        if not formatStr:
            formatStr = '%f\t' * nCols + '\n'
        elif not formatStr.endswith('\n'):
            formatStr += '\n'

        while self.runFlag:
            # Create the log file.#
            fileName = time.strftime(self.fileSettings.get('filenameStr'),
                                     time.localtime())
            filePath = os.path.join('/var/lib/LabJackTemperatureLogger',
                                    fileName)

            headings = self.fileSettings.get('headings')
            if headings:
                with open(fileName, 'w') as fh:
                    fstr = '%s \t' * len(headings)
                    fh.write(fstr % tuple(headings))
                    fh.write('\n')

            nlines = 0
            while nlines < self.max_log_size:
                nlines+=1
                if len(self.queue) == 0:
                    # No data to process. Wait then skip to next iteration.
                    time.sleep(1)
                    continue

                # There is data to process.
                # Fetch oldest point in queue.
                with self.lock:
                    newData = self.queue.popleft()
                # Throw away extra columns.
                newData[nCols:] = []
                # Log data to file.
                with open(fileName, 'a') as fh:
                    fh.write(formatStr % newData)


class Acquirer(StartStopThread):
    def __init__(self, period, daqFunc, callbackFunc):
        """Acquires data at specific time interval and does stuff with it.
        Args:
            period (float) - time interval between acquisitions in seconds.
              No point in setting to less than 0.01 seconds.
            Container (*daqFunc) (void) - function to perform acquisition.
            void (*callbackFunc) (float, Container) - function that will act
              on the current time (in seconds) and the acquired data.
        """
        super(Acquirer, self).__init__()
        self.period = period
        self.daqFunc = daqFunc
        self.callbackFunc = callbackFunc
        self.last = None

    def run(self):
        tLast = 0
        t0 = time.time()
        while self.runFlag:
            tNow = time.time()
            if tNow >= tLast + self.period:
                data = self.daqFunc()
                tLast = tNow
                self.last = data
                if not isinstance(data, Container):
                    data = (data,)
                self.callbackFunc(tNow, *data)
            time.sleep(0.01)

def test():
    import random
    dh = DataHandler()
    dh.start()

    dummySource = lambda: random.randint(0, 100)
    daq = Acquirer(1, dummySource, dh.addToQueue)
    daq.start()

    plotter = Plotter(5, dh.getLongHistory)
    plotter.start()

    return (plotter, daq, dh)
