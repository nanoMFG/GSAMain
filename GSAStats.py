import pandas as pd
import pyqtgraph as pg
import numpy as np
from pandas.api.types import is_numeric_dtype
import copy
from PyQt5 import QtGui, QtCore
from GSAImage import GSAImage

class GSAStats(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAStats,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.df = pd.DataFrame()

		self.scatter = pg.ScatterPlotWidget()
		self.layout.addWidget(self.scatter,0,0)

	def setData(self,df):
		self.df = df
		if len(self.df) > 0:
			scatter_df = copy.deepcopy(self.df)
			for c in scatter_df.columns:
				if not is_numeric_dtype(scatter_df[c]):
					scatter_df.drop(c,axis=1,inplace=True)
			scatter_array = np.core.records.fromarrays([scatter_df[c].values for c in scatter_df.columns],names=[c for c in scatter_df.columns])
			self.scatter.setData(scatter_array)
			self.scatter.setFields([(field,{'mode':'range'}) for field in scatter_df.columns])
		else:
			self.scatter.setData(None)
