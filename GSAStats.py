import pandas as pd
import pyqtgraph as pg
import numpy as np
from pandas.api.types import is_numeric_dtype
import copy
from sklearn.manifold import TSNE
from PyQt5 import QtGui, QtCore
from gresq.database import sample, preparation_step, dal, Base
from models import ItemsetsTableModel, ResultsTableModel

class PlotWidget(QtGui.QWidget):
	def __init__(self,parent=None):
		super(PlotWidget,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.model = ResultsTableModel()


		self.xaxisbox = QtGui.QComboBox()
		self.yaxisbox = QtGui.QComboBox()
		self.zaxisbox = QtGui.QComboBox()
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

	def setModel(self,model):
		self.model = model
		self.yaxisbox.clear()
		self.xaxisbox.clear()
		for c in self.model.df.columns:
			if is_numeric_dtype(self.model.df[c]):
				self.xaxisbox.addItem(c)
				self.yaxisbox.addItem(c)

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

class TSNEWidget(QtGui.QStackedWidget):
	def __init__(self,parent=None):
		super(TSNEWidget,self).__init__(parent=parent)
		self.itemsets_model = ItemsetsTableModel()

		self.tsne = TSNEPlot()
		self.feature = FeatureSelectionItem()
		self.addWidget(self.feature)
		self.addWidget(self.tsne)

		self.tsne.run_button.clicked.connect(
			lambda: self.tsne.run(self.feature.get_selected_features()))
		self.feature.go_button.clicked.connect(lambda: self.setCurrentWidget(self.tsne))
		self.tsne.back_button.clicked.connect(lambda: self.setCurrentWidget(self.feature))

	def setModel(self,model):
		self.results_model = model
		self.itemsets_model.update_frequent_itemsets(
			df=model.df.select_dtypes(include=[np.number]),
			min_support=float(self.feature.min_support_edit.text())
			)
		self.feature.setModel(self.itemsets_model)
		self.tsne.setModel(self.results_model)
		
class TSNEPlot(QtGui.QWidget):
	def __init__(self,parent=None):
		super(TSNEPlot,self).__init__(parent=parent)
		self.model = ResultsTableModel()

		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.random_seed = np.random.randint(1,99999)
		self.plot_widget = pg.PlotWidget()
		self.tsne_plot = pg.ScatterPlotItem(symbol="o", size=10, pen=pg.mkPen(0.2),brush=pg.mkBrush(0.7),antialias=True)
		self.plot_widget.hideAxis('left')
		self.plot_widget.hideAxis('bottom')
		self.plot_widget.addItem(self.tsne_plot)
		
		self.random_seed_edit = QtGui.QLineEdit(str(self.random_seed))
		self.random_seed_edit.setValidator(QtGui.QIntValidator(1,99999))

		self.select_feature = QtGui.QComboBox()

		self.run_button = QtGui.QPushButton('Run t-SNE')
		self.back_button = QtGui.QPushButton('<<< Feature Selection')
		self.save_button = QtGui.QPushButton('')
		self.save_button.setIcon(self.style().standardIcon(QtGui.QStyle.SP_FileDialogStart))
		self.save_button.setMaximumWidth(50)

		self.layout.addWidget(self.select_feature,0,0,1,2)
		self.layout.addWidget(self.plot_widget,1,0,1,2)
		self.layout.addWidget(self.run_button,2,1)
		self.layout.addWidget(self.back_button,2,0)
		self.layout.addWidget(self.save_button,3,0)

		self.select_feature.activated[str].connect(self.setBrushes)

	def setModel(self,model):
		self.model = model
		self.select_feature.clear()
		self.select_feature.addItem('No Coloring')
		self.select_feature.addItems(list(self.model.df.columns))

	def setBrushes(self,feature):
		if feature in self.model.df.columns:
			brushes = []
			if is_numeric_dtype(self.model.df[feature]):
				values = self.model.df[feature][self.nonnull_indexes]
				maxVal = max(values)
				minVal = min(values)
				for val in values:
					if ~pd.isnull(val):
						index  = int((val-minVal)/(maxVal-minVal)*100)
						brushes.append(pg.mkBrush(pg.intColor(index=index,values=100)))
					else:
						brushes.append(pg.mkBrush(0.2))
			else:
				values = self.model.df[feature].unique()
				for v,val in enumerate(values):
					if ~pd.isnull(val):
						index = int(v/len(values)*100)
						brushes.append(pg.mkBrush(pg.intColor(index=index,values=100)))
					else:
						brushes.append(pg.mkBrush(0.2))
			self.tsne_plot.setBrush(brushes)

	def run(self,features):
		self.features = features
		self.tsne = TSNE(random_state=self.random_seed)
		self.nonnull_indexes = ~self.model.df[self.features].isnull().any(1)
		self.tsne.fit(self.model.df[self.features][self.nonnull_indexes])
		self.tsne_plot.setData(x=self.tsne.embedding_[:,0],y=self.tsne.embedding_[:,1])

class FeatureSelectionItem(QtGui.QWidget):
	def __init__(self,parent=None):
		super(FeatureSelectionItem,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.feature_list = QtGui.QListWidget()
		self.feature_list.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

		self.min_support = 0.5
		
		self.model = ItemsetsTableModel()
		self.itemsets_view = QtGui.QTableView()
		self.itemsets_view.verticalHeader().setVisible(False)
		self.itemsets_view.setMinimumHeight(200)
		self.itemsets_view.setMinimumWidth(300)
		self.itemsets_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.itemsets_view.setSortingEnabled(True)
		self.itemsets_view.activated.connect(lambda x: self.select_features(self.model,x))

		self.min_support_edit = QtGui.QLineEdit(str(self.min_support))
		self.min_support_edit.setFixedWidth(75)
		self.min_support_edit.setValidator(QtGui.QDoubleValidator(0,1,3))

		self.go_button = QtGui.QPushButton('Go to Plot >>>')

		self.layout.addWidget(QtGui.QLabel('Minimum Support'),0,0)
		self.layout.addWidget(self.min_support_edit,1,0)
		self.layout.addWidget(self.itemsets_view,2,0)
		self.layout.addWidget(QtGui.QLabel('Manual Feature Selection'),3,0)
		self.layout.addWidget(self.feature_list,4,0)
		
		self.layout.addWidget(self.go_button,11,0,1,1)

	def setModel(self,model):
		self.model = model
		self.itemsets_view.setModel(self.model)
		header = self.itemsets_view.horizontalHeader()
		header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
		header.setStretchLastSection(True)
		self.feature_list.clear()
		self.feature_list.addItems(self.model.items)

	def select_features(self,model,index):
		self.feature_list.clearSelection()
		for item in model.frequent_itemsets['Feature Set'].iloc[index.row()]:
			list_item = self.feature_list.findItems(item,QtCore.Qt.MatchExactly)[0]
			list_item.setSelected(True)

	def get_selected_features(self):
		return [s.text() for s in self.feature_list.selectedItems()]
