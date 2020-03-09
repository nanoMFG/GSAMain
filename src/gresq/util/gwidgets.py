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
from mlxtend.frequent_patterns import apriori
import functools
from gresq.database.models import Sample
import logging
from sqlalchemy import String, Integer, Float, Numeric, Date
from collections.abc import Sequence
from collections import OrderedDict, deque
import pyqtgraph as pg

logger = logging.getLogger(__name__)

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


class SpacerMaker:
    def __init__(self,vexpand=True,hexpand=True,width=None,height=None):
        if vexpand == True:
            self.vexpand = QtGui.QSizePolicy.Ignored
        else:
            self.vexpand = QtGui.QSizePolicy.Preferred

        if hexpand == True:
            self.hexpand = QtGui.QSizePolicy.Ignored
        else:
            self.hexpand = QtGui.QSizePolicy.Preferred

        self.width = width
        self.height = height


    def __call__(self):
        if isinstance(self.width,int):
            width = self.width
        else:
            width = BasicLabel().sizeHint().width()
        if isinstance(self.height,int):
            height = self.height
        else:
            height = BasicLabel().sizeHint().height()

        spacer = QtGui.QSpacerItem(
            width,
            height,
            vPolicy=self.vexpand,
            hPolicy=self.hexpand
        )

        return spacer


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
    def __init__(self,border=False,parent=None):
        QtWidgets.QStackedWidget.__init__(self,parent=parent)
        self.meta = OrderedDict()
        if border == True:
            self.setFrameStyle(QtGui.QFrame.StyledPanel)
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

    def index(self,key):
    	return list(self.meta.keys()).index(key)

    def clear(self):
        while self.count()>0:
            self.removeIndex(0)

    def widget(self,key):
    	if isinstance(key,int):
    		return QtWidgets.QStackedWidget.widget(self,key)
    	elif isinstance(key,str):
    		if key in self.meta.keys():
    			key = self.index(key)
    			return QtWidgets.QStackedWidget.widget(self,key)
    		else:
    			raise ValueError("Key '%s' not in metadict!"%key)
    	else:
    		raise ValueError("Key '%s' is type '%s'. Keys must be type 'int' or 'str'!"%(key,type(key)))


class ImageWidget(pg.GraphicsLayoutWidget):
    def __init__(self, path, parent=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.viewbox = self.addViewBox(row=1, col=1)
        self.img_item = pg.ImageItem()
        self.viewbox.addItem(self.img_item)
        self.viewbox.setAspectLocked(True)
        self.viewbox.setMouseEnabled(False,False)

        img = np.array(Image.open(path))
        self.img_item.setImage(img, levels=(0, 255))

        self.viewbox.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)