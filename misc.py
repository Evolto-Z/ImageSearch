import math
import cv2 as cv
import numpy as np
from PyQt6.QtCore import *
import traceback, sys


def adaptSizeToLimitedSize(w, h, limitedW, limitedH, upperBound=True, toLimit=False):
    ratio_w = limitedW / w
    ratio_h = limitedH / h
    ratio = 1
    if upperBound:
        ratio = min(ratio_h, ratio_w)
        if not toLimit and ratio >= 1:
            return w, h
    else:
        ratio = max(ratio_h, ratio_w)
        if not toLimit and ratio <= 1:
            return w, h
    w = math.floor(ratio * w)
    h = math.floor(ratio * h)
    return w, h


def calcPHash(img):
        img = cv.resize(img, (32, 32), interpolation=cv.INTER_AREA)
        img = cv.cvtColor(img, cv.COLOR_RGBA2GRAY)
        dct = cv.dct(img.astype(np.float32))
        thumbnail = dct[0:8, 0:8]
        mean = thumbnail.mean()
        pHash = 0
        for i in range(8):
            for j in range(8):
                if thumbnail[i, j] >= mean:
                    idx = j + i * 8
                    pHash |= (1 << idx)
        return pHash


def calcHammingDist(bits1, bits2):
    bits = bits1 ^ bits2
    dist = 0
    while bits > 0:
        dist += 1
        bits &= (bits - 1)
    return dist


def alphaBlendAntiBG(img):
    h, w, _ = img.shape
    
    alpha = img[:, :, -1].astype(np.float32) / 255
    alpha = np.stack([alpha, alpha, alpha], -1)
    img = img[:, :, :3].astype(np.float32)
    pure = np.ones((h, w, 3), np.float32)
    pure *= 255 - img.mean()
    blended = pure * (1 - alpha) + img * alpha
    blended = blended.astype(np.uint8)

    return blended


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done