import os
import numpy as np
from PIL import Image
from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import copy
import io
import operator
import requests
import traceback
import inspect
import functools
from gresq.database.models import Sample
from gresq.util.util import errorCheck
import logging
from sqlalchemy import String, Integer, Float, Numeric, Date
from collections.abc import Sequence
from collections import OrderedDict, deque
import pyqtgraph as pg

logger = logging.getLogger(__name__)

class DownloadThread(QtCore.QThread):
    """
    Threading class for downloading files. Can be used to download files in parallel.

    url:                    Box download url.
    thread_id:              Thread ID that used to identify the thread.
    info:                   Dictionary for extra parameters.
    """

    downloadFinished = QtCore.pyqtSignal(object, int, object)

    def __init__(self, url, thread_id, info={}):
        super(DownloadThread, self).__init__()
        self.url = url
        self.thread_id = thread_id
        self.info = info
        self.data = None

        self.finished.connect(self.signal())

    def __del__(self):
        self.wait()

    def signal(self):
        self.downloadFinished.emit(self.data, self.thread_id, self.info)

    def run(self):
        r = requests.get(self.url)
        self.data = r.content

class DownloadRunner(QtCore.QObject):
    """
    Allows for download interruption by intercepting and preventing signal. Does not actually terminate thread.
    """
    finished = QtCore.pyqtSignal([],[object, int, object])
    terminated = QtCore.pyqtSignal()
    def __init__(self,url,thread_id, info={}):
        self.thread = DownloadThread(url,thread_id,info)
        self.interrupted = False

        self.thread.downloadFinished.connect(self.sendSignal)

    def sendSignal(self,*args):
        if self.interrupted == False:
            self.finished[object, int, object].emit(*args)
            self.finished.emit()

    def interrupt(self):
        self.interrupted = True
        self.terminated.emit()

    def start(self):
        self.thread.start()

class DownloadPool(QtCore.QObject):
    """
    Thread pooler for handling download threads

    max_thread_count:           (int) Max number of threads running at once.
    """
    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    terminated = QtCore.pyqtSignal()
    def __init__(self,max_thread_count=1):
        super(DownloadPool,self).__init__()
        self.max_thread_count = max_thread_count
        self._count = 0
        self.queue = deque()
        self.running = []

    def maxThreadCount(self):
        return self.max_thread_count

    def count(self):
        return self._count

    def queueCount(self):
        return len(self.queue)

    def runCount(self):
        return len(self.running)

    def doneCount(self):
        return self.count() - self.runCount() - self.queueCount()

    def addRunner(self,runner):
        assert isinstance(runner,DownloadRunner)
        # 'terminated' signal tells all runners to prevent DownloadThread 'finished' signal from emitting
        self.terminated.connect(runner.interrupt)

        self.queue.append(runner)
        self._count += 1

    def runNext(self):
        if len(self.queue) > 0 and len(self.running) <= self.max_thread_count:
            runner = self.queue.popleft()

            self.running.append(runner)
            # When runner is interrupted or its DownloadThread finishes, thread is removed from pool
            runner.terminated.connect(lambda: self.running.remove(runner) if runner in self.running else None)
            runner.terminated.connect(lambda: self.queue.remove(runner) if runner in self.queue else None)
            # When thread finishes, run next thread in queue
            runner.finished.connect(self.runNext)
            runner.start()
        elif len(self.running) == 0:
            self.finished.emit()

    def run(self):
        self.started.emit()
        while len(self.running) < self.max_thread_count and len(self.queue) > 0:
            self.runNext()

    def terminate(self):
        self.terminated.emit()
        self._count = 0



class IO(QtWidgets.QWidget):
    def __init__(self,config,imptext="Import",exptext="Export",parent=None):
        super(IO,self).__init__(parent=parent)
        self.config = config
        self.import_button = QtWidgets.QPushButton(imptext)
        self.export_button = QtWidgets.QPushButton(exptext)

    @errorCheck(error_text="Error importing file!")
    def importFile(self):
        if self.config.mode == "local":
            file_path = QtGui.QFileDialog.getOpenFileName()
            if isinstance(file_path, tuple):
                file_path = file_path[0]
            else:
                return
            return file_path
        elif self.config.mode == "nanohub":
            file_path = (
                subprocess.check_output("importfile", shell=True)
                .strip()
                .decode("utf-8")
            )
            return file_path
        else:
            return

    @errorCheck(error_text="Error exporting file!")
    def exportFile(self,default_filename=None,extension=None):
        if isinstance(extension,str):
            extension = extension.strip('.')
        if isinstance(default_filename,str):
            filename = default_filename
        else:
            filename = 'untitled'
            if isinstance(extension,str):
                filename = filename + ".%s"extension

        directory = os.path.join(os.getcwd(),filename)
        if self.config.mode == 'local':
            if isinstance(extension,str):
                filt = "File Type (*.%s)"%extension
            else:
                filt = ''
            name = QtWidgets.QFileDialog.getSaveFileName(None, 
                caption="Export Image", 
                dir=directory,
                filter=filt)[0]
            if name != '':
                with open(name,'w') as f:
                    json.dump(self.recipe_model.json_encodable(),f)
        elif self.config.mode == 'nanohub':
            with open(filename,'w') as f:
                json.dump(self.recipe_model.json_encodable(),f)
            subprocess.check_output('exportfile %s'%filename,shell=True)
            os.remove(name)

def downloadAllImageMasks(session, directory):
    def saveTo(data, path):
        with open(path, "wb") as f:
            f.write(data)

    for sample_model in session.query(Sample).all():
        for analysis in sample_model.analyses:
            sem = analysis.sem_file_model
            mask_url = analysis.mask_url
            img_url = sem.url

            par_path = os.path.join(directory, sample_model)
            thread = DownloadThread(img_url, sample_model.id)
            thread.downloadFinished.connect(lambda x, y, z: saveTo)