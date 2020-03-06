import os
from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import copy
import io
import operator
import requests
import traceback
import inspect
from mlxtend.frequent_patterns import apriori
import functools
from gresq.database.models import Sample
import logging
from sqlalchemy import String, Integer, Float, Numeric, Date
from collections.abc import Sequence
from collections import OrderedDict, deque

logger = logging.getLogger(__name__)

sql_validator = {
    "int": lambda x: isinstance(x.property.columns[0].type, Integer),
    "float": lambda x: isinstance(x.property.columns[0].type, Float),
    "str": lambda x: isinstance(x.property.columns[0].type, String),
    "date": lambda x: isinstance(x.property.columns[0].type, Date),
}

operators = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


class ConfigParams:
    def __init__(self,box_config_path=None,mode='local',read=True,write=False,validate=False,test=False):
        assert mode in ['local','nanohub']
        self.box_config_path = box_config_path
        self.mode = mode
        self.read = read
        self.write = write
        self.validate = validate
        self.test = test

    def canRead(self):
        return self.read

    def canWrite(self):
        return self.write

    def canValidate(self):
        return self.validate

    def canRead(self):
        return self.read

    def setRead(self,flag):
        assert isinstance(flag,bool)
        self.read = flag

    def setWrite(self,flag):
        assert isinstance(flag,bool)
        self.write = flag

    def setValidate(self,flag):
        assert isinstance(flag,bool)
        self.validate = flag

class Label(QtWidgets.QLabel):
    def __init__(self,text='',tooltip=None):
        super(Label,self).__init__()
        self.tooltip = tooltip
        if text is None:
            text = ''
        self.setText(text)
        if isinstance(self.tooltip,str):
            self.setMouseTracking(True)

    def setMouseTracking(self,flag):
        """
        Ensures mouse tracking is allowed for label and all parent widgets 
        so that tooltip can be displayed when mouse hovers over it.
        """
        QtWidgets.QWidget.setMouseTracking(self, flag)
        def recursive(widget,flag):
            try:
                if widget.mouseTracking() != flag:
                    widget.setMouseTracking(flag)
                    recursive(widget.parent(),flag)
            except:
                pass
        recursive(self.parent(),flag)

    def event(self,event):
        if event.type() == QtCore.QEvent.Leave:
            QtWidgets.QToolTip.hideText()
        return QtWidgets.QLabel.event(self,event)

    def mouseMoveEvent(self,event):
        QtWidgets.QToolTip.showText(
            event.globalPos(),
            self.tooltip
            )

class LabelMaker:
    def __init__(self,family=None,size=None,bold=False,italic=False):
        self.family = family
        self.size = size
        self.bold = bold
        self.italic = italic

    def __call__(self,text='',tooltip=None):
        label = Label(text,tooltip=tooltip)
        font = QtGui.QFont()
        if self.family:
            font.setFamily(self.family)
        if self.size:
            font.setPointSize(self.size)
        if self.bold:
            font.setBold(self.bold)
        if self.italic:
            font.setItalic(self.italic)
        label.setFont(font)

        return label


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
        if self.sendSignal:
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
    def __init__(self,url, thread_id, info={}):
        self.thread = DownloadThread(url,thread_id,info)
        self.interrupted = False

        self.thread.finished.connect(self.sendSignal)

    def sendSignal(self,*args):
        if not self.interrupted:
            self.finished[object, int, object].emit(*args)
            self.finished.emit()

    def interrupt(self):
        self.interrupted = True
        self.terminated.emit()

    def start(self):
        self.thread.start()

class DownloadPool:
    """
    Thread pooler for handling download threads
    """
    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    terminated = QtCore.pyqtSignal()
    def __init__(self,max_thread_count=1):
        self.max_thread_count = max_thread_count
        self.queue = deque()
        self.running = []

    def maxThreadCount(self):
        return self.max_thread_count

    def addThread(self,runner):
        # 'terminated' signal tells all runners to prevent DownloadThread 'finished' signal from emitting
        self.terminated.connect(runner.interrupt)

        self.queue.append(runner)

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
        while len(self.running) < self.max_thread_count and len(self.queue) > 0:
            self.runNext()

    def terminate(self):
        self.terminated.emit()



class ItemsetsTableModel(QtCore.QAbstractTableModel):
    """
    Creates a PyQt TableModel that determines the support for different sets of attributes.
    If all rows contain data for a set of attributes, the support is '1' and if no rows contain
    data for a set, the support is '0'. This model is useful for conducting analyses on
    datasets where some rows are missing data. It can help determine which sets of attributes
    should be used on the basis of how much support there is for a particular set.
    """

    def __init__(self, parent=None):
        super(ItemsetsTableModel, self).__init__(parent=parent)
        self.frequent_itemsets = pd.DataFrame()
        self.items = []

    def rowCount(self, parent):
        return self.frequent_itemsets.shape[0]

    def columnCount(self, parent):
        return self.frequent_itemsets.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i, j = index.row(), index.column()
                value = self.frequent_itemsets.iloc[i, j]
                if pd.isnull(value):
                    return ""
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.frequent_itemsets.columns[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.frequent_itemsets.sort_values(
                by=self.frequent_itemsets.columns[column], ascending=True, inplace=True
            )
        elif order == QtCore.Qt.DescendingOrder:
            self.frequent_itemsets.sort_values(
                by=self.frequent_itemsets.columns[column], ascending=False, inplace=True
            )
        self.layoutChanged.emit()

    def update_frequent_itemsets(self, df, min_support=0.5):
        self.beginResetModel()
        dfisnull = ~pd.isnull(df)
        self.items = df.columns
        self.frequent_itemsets = apriori(dfisnull, use_colnames=True, min_support=0.5)
        self.frequent_itemsets.columns = ["Support", "Feature Set"]
        self.frequent_itemsets["# Features"] = self.frequent_itemsets[
            "Feature Set"
        ].apply(lambda x: len(x))
        self.frequent_itemsets["Feature Set"] = self.frequent_itemsets[
            "Feature Set"
        ].apply(lambda x: tuple(x))
        self.frequent_itemsets["Support"] = self.frequent_itemsets["Support"].apply(
            lambda x: round(x, 4)
        )
        self.frequent_itemsets.sort_values(
            by="# Features", ascending=False, inplace=True
        )
        self.frequent_itemsets = self.frequent_itemsets[
            ["Support", "# Features", "Feature Set"]
        ]
        self.endResetModel()


class ResultsTableModel(QtCore.QAbstractTableModel):
    """
    This PyQt TableModel is used for displaying data queried from a SQL query 
    in a TableView.
    """

    def __init__(self, parent=None):
        super(ResultsTableModel, self).__init__(parent=parent)
        self.df = pd.DataFrame()
        self.header_mapper = None

    def copy(self, fields=None):
        model = ResultsTableModel()
        model.df = self.df.copy()
        model.header_mapper = copy.deepcopy(self.header_mapper)

        if fields:
            for col in model.df.columns:
                if col not in fields:
                    model.df.drop(columns=col, inplace=True)
                    del model.header_mapper[col]

        return model

    def setHeaderMapper(self, models):
        self.header_mapper = {}
        for column in list(self.df.columns):
            for model in models:
                if hasattr(model, column):
                    info = getattr(model, column).info
                    if "verbose_name" in info:
                        value = info["verbose_name"]
                    else:
                        logger.warning(
                            f"column: {column} in {model.__name__} has no verbose_name in info."
                        )
                        value = column
                    if "std_unit" in info:
                        if info["std_unit"]:
                            value += " (%s)" % info["std_unit"]
                    self.header_mapper[column] = value
                    break

    def read_sqlalchemy(self, statement, session, models=None):
        self.beginResetModel()
        self.df = pd.read_sql_query(statement, session.connection())

        if models:
            self.setHeaderMapper(models)
        else:
            self.header_mapper = None

        self.endResetModel()

    def value(self, column, row):
        if isinstance(column, str):
            item = self.df[column]
            return item.iloc[row].values[0]

    def rowCount(self, parent):
        return self.df.shape[0]

    def columnCount(self, parent):
        return self.df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                i, j = index.row(), index.column()
                value = self.df.iloc[i, j]
                if pd.isnull(value):
                    return ""
                else:
                    return str(value)
        return QtCore.QVariant()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if self.header_mapper:
                return self.header_mapper[self.df.columns[section]]
            else:
                return self.df.columns[section]

        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.AscendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column], ascending=True)
        elif order == QtCore.Qt.DescendingOrder:
            self.df = self.df.sort_values(by=self.df.columns[column], ascending=False)
        self.layoutChanged.emit()


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


def errorCheck(success_text=None, error_text="Error!",logging=True,show_traceback=False):
    """
    Decorator for class functions to catch errors and display a dialog box for a success or error.
    Checks if method is a bound method in order to properly handle parents for dialog box.

    success_text:               (str) What header to show in the dialog box when there is no error. None displays no dialog box at all.
    error_text:                 (str) What header to show in the dialog box when there is an error.
    logging:                    (bool) Whether to write error to log. True writes to log, False does not.
    show_traceback:             (bool) Whether to display full traceback in error dialog box. 
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if inspect.ismethod(func):
                self = args[0]
            else:
                self = None
            try:
                return func(*args, **kwargs)
                if success_text:
                    success_dialog = QtWidgets.QMessageBox(self)
                    success_dialog.setText(success_text)
                    success_dialog.setWindowModality(QtCore.Qt.WindowModal)
                    success_dialog.exec()
            except Exception as e:
                error_dialog = QtWidgets.QMessageBox(self)
                error_dialog.setWindowModality(QtCore.Qt.WindowModal)
                error_dialog.setText(error_text)
                if logging:
                    logging.exception(traceback.format_exc())
                elif show_traceback:
                    error_dialog.setInformativeText(traceback.format_exc())
                else:
                    error_dialog.setInformativeText(str(e))
                error_dialog.exec()

        return wrapper
    return decorator

class ConfirmationBox(QtWidgets.QMessageBox):
    okSignal = QtCore.pyqtSignal()
    cancelSignal = QtCore.pyqtSignal()
    def __init__(self,question_text,informative_text=None,parent=None):
        super(ConfirmationBox,self).__init__(self,parent=parent)
        assert isinstance(question_text,str)

        self.setText(question_text)
        if informative_text:
            self.setInformativeText(informative_text)
        self.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )
        self.setWindowModality(QtCore.Qt.WindowModal)

        self.buttonClicked.connect(self.onClick)

    def onClick(self,btn):
        if btn.text() == "OK":
            self.okSignal.emit()
        else:
            self.cancelSignal.emit()    

class GStackedMeta(type(QtWidgets.QStackedWidget),type(Sequence)):
    pass

class GStackedWidget(QtWidgets.QStackedWidget,Sequence,metaclass=GStackedMeta):
    widgetAdded = QtCore.pyqtSignal(str)
    def __init__(self,parent=None):
        QtWidgets.QStackedWidget.__init__(self,parent=parent)
        self.meta = OrderedDict()

        self.widgetRemoved.connect(lambda i: self.meta.pop(list(self.meta.keys())[i]))
        self.widgetAdded.connect(lambda s: self.meta.update({s:{}}))

    def __getitem__(self,key):
        if key < self.count():
            return self.widget(key)
        else:
            raise IndexError("Index %s out of range for GStackedWidget with length %s"%(key,self.count()))

    def __len__(self):
        return self.count()

    def createListWidget(self):
        list_widget = QtWidgets.QListWidget()
        for name in self.meta.keys():
            list_widget.addItem(name)
        
        self.widgetAdded.connect(list_widget.addItem)
        self.widgetRemoved.connect(list_widget.takeItem)
        self.currentChanged.connect(list_widget.setCurrentRow)

        list_widget.currentRowChanged.connect(self.setCurrentIndex)

        return list_widget

    def addWidget(self,widget,name=None,focus_slot=None,metadict=None):
        QtWidgets.QStackedWidget.addWidget(self,widget)
        
        if callable(focus_slot):
            self.currentChanged.connect(focus_slot)
        elif focus_slot is not None:
            raise TypeError("Parameter 'focus_slot' must be a callable function!")

        if not isinstance(name,str):
            name = "%s - %s"%(widget.__class__.__name__,self.count()-1)
        self.widgetAdded.emit(name)
        
        if metadict is not None:
            self.meta[name].update(metadict)

        return self.count()-1

    def removeIndex(self,index):
        QtWidgets.QStackedWidget.removeWidget(self,self.widget(index))

    def removeCurrentWidget(self):
        widget = self.currentWidget()
        if widget != 0:
            QtWidgets.QStackedWidget.removeWidget(self,widget)

    def changeNameByIndex(self,index,name):
        assert isinstance(index,int)
        assert isinstance(name,str)
        self.meta = OrderedDict([(name, item[1]) if i == index else item for i, item in enumerate(self.meta.items())])

    def getMetanames(self):
        return self.meta.keys()

    def metaname(self,index):
        return list(self.meta.keys())[index]

    def clear(self):
        while self.count()>0:
            self.removeIndex(0)


class ImageWidget(pg.GraphicsLayoutWidget):
    def __init__(self, path, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.viewbox = self.addViewBox(row=1, col=1)
        self.img_item = pg.ImageItem()
        self.viewbox.addItem(self.img_item)
        self.viewbox.setAspectLocked(True)

        img = np.array(Image.open(path))
        self.img_item.setImage(img, levels=(0, 255))

HeaderLabel = LabelMaker(family='Helvetica',size=28,bold=True)
SubheaderLabel = LabelMaker(family='Helvetica',size=18)
BasicLabel = LabelMaker()
