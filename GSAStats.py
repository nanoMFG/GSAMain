import pandas as pd
import pyqtgraph as pg
import numpy as np
from pandas.api.types import is_numeric_dtype
import copy
from PyQt5 import QtGui, QtCore
from gresq.database import sample, preparation_step, dal, Base
from GSAImage import GSAImage

class GSAStats(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAStats,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.df = pd.DataFrame()


		self.xaxisbox = QtGui.QComboBox()
		self.yaxisbox = QtGui.QComboBox()
		self.plot_widget = pg.PlotWidget()
		self.scatter_plot = pg.ScatterPlotItem()
		self.plot_widget.addItem(self.scatter_plot)

		self.xaxisbox.activated.connect(self.updatePlot)
		self.yaxisbox.activated.connect(self.updatePlot)

		self.layout.addWidget(QtGui.QLabel('X Axis'),0,0,1,1)
		self.layout.addWidget(QtGui.QLabel('Y Axis'),0,1,1,1)
		self.layout.addWidget(self.xaxisbox,1,0,1,1)
		self.layout.addWidget(self.yaxisbox,1,1,1,1)
		self.layout.addWidget(self.plot_widget,2,0,1,2)

	def setData(self,df):
		self.df = df
		for c in self.df.columns:
			if not is_numeric_dtype(self.df[c]):
				self.df.drop(c,inplace=True,axis=1)
		self.xaxisbox.addItems(self.df.columns)
		self.yaxisbox.addItems(self.df.columns)

	def updatePlot(self):
		x = self.xaxisbox.currentText()
		y = self.yaxisbox.currentText()
		scatter_data = self.df.loc[:,[x,y]].dropna()
		if x != y:
			self.scatter_plot.setData(x=scatter_data[x],y=scatter_data[y])
		else:
			self.scatter_plot.setData(x=scatter_data.iloc[:,0],y=scatter_data.iloc[:,0])
		
		xbounds = self.scatter_plot.dataBounds(ax=0)
		if None not in xbounds:
			self.plot_widget.setXRange(*xbounds)
		ybounds = self.scatter_plot.dataBounds(ax=1)
		if None not in ybounds:
			self.plot_widget.setYRange(*ybounds)
		self.plot_widget.setLabel(text=x,axis='bottom')
		self.plot_widget.setLabel(text=y,axis='left')

class GSAVisualize(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAVisualize,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.plot_widget = pg.PlotWidget()
		self.tsne_plot = pg.ScatterPlotItem()

		self.kl_div_label = QtGui.QLabel()
		self.run_button = QtGui.QPushButton('Run t-SNE')
		self.feature_box = QtGui.QComboBox()

	def setData(self,df):
		self.df = df
		for c in self.df.columns:
			if not is_numeric_dtype(self.df[c]):
				self.df.drop(c,inplace=True,axis=1)
		self.feature_box.addItems(self.df.columns)







