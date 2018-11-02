import pandas as pd
import pyqtgraph as pg
import numpy as np
from pandas.api.types import is_numeric_dtype
import copy
from mlxtend.frequent_patterns import apriori
from sklearn.manifold import TSNE
from PyQt5 import QtGui, QtCore
from gresq.database import sample, preparation_step, dal, Base
from GSAImage import GSAImage

class PlotWidget(QtGui.QWidget):
	def __init__(self,parent=None):
		super(PlotWidget,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.df = pd.DataFrame()


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

	def setData(self,df):
		self.df = df
		for c in self.df.columns:
			if not is_numeric_dtype(self.df[c]):
				self.df.drop(c,inplace=True,axis=1)
		self.yaxisbox.clear()
		self.xaxisbox.clear()
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

class TSNEWidget(QtGui.QTabWidget):
	def __init__(self,parent=None):
		super(TSNEWidget,self).__init__(parent=parent)
		self.itemsets_model = ItemsetsTableModel()

		self.tsne_tab = TSNEItem()
		self.feature_tab = FeatureSelectionItem()
		self.addTab(self.feature_tab,'Select Features')
		self.addTab(self.tsne_tab,'t-SNE Plot')

		self.tsne_tab.run_button.clicked.connect(lambda: self.tsne_tab.run(self.feature_tab.get_selected_features()))

class TSNEItem(QtGui.QWidget):
	def __init__(self,parent=None):
		super(TSNEItem,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.numeric_df = pd.DataFrame()
		self.class_df = pd.DataFrame()

		self.random_seed = np.random.randint(1,99999)
		self.plot_widget = pg.PlotWidget()
		self.tsne_plot = pg.ScatterPlotItem()
		
		self.random_seed_edit = QtGui.QLineEdit(str(self.random_seed))
		self.random_seed_edit.setValidator(QtGui.QIntValidator(1,99999))

		self.run_button = QtGui.QPushButton('Run t-SNE')
		self.feature_box = QtGui.QComboBox()


	def setData(self,df):
		self.numeric_df = copy.deepcopy(df)
		self.class_df = copy.deepcopy(df)
		for c in df.columns:
			if not is_numeric_dtype(df[c]):
				self.numeric_df.drop(c,inplace=True,axis=1)
			else:
				self.class_df.drop(c,inplace=True,axis=1)
		# self.feature_box.addItems(self.numeric_df.columns+self.class_df.columns)
		self.itemsets_model.update_frequent_itemsets(df=self.numeric_df,min_support=float(self.min_support_edit.text()))

	def run(self,df):
		if len(self.numeric_df)>1 and len(selected_items)>2:
			columns = [i.text() for i in selected_items]
			try:
				self.tsne = TSNE(random_state=self.random_seed)
				self.tsne.fit(self.numeric_df[columns].values)
				self.kl_div_label.setText(str(self.tsne.kl_divergence_))
				self.tsne_plot.setData(x=self.tsne.embedding_[:,0],y=self.tsne.embedding_[:,1])
			except:
				pass

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
		self.min_support_edit.setValidator(QtGui.QDoubleValidator(0,1,3))

		self.layout.addWidget(QtGui.QLabel('Selected Features'),0,0,1,1)
		self.layout.addWidget(self.feature_list,1,0,4,1)
		self.layout.addWidget(QtGui.QLabel('Minimum Support'),1,1,1,1)
		self.layout.addWidget(self.min_support_edit,2,2,1,1)
		self.layout.addWidget(self.itemsets_view,5,0,3,3)

	def setModel(self,model):
		self.model = model
		self.itemsets_view.setModel(self.model)
		self.feature_list.clear()
		self.feature_list.addItems(self.model.items)

	def select_features(self,model,index):
		self.feature_list.clearSelection()
		for item in model.frequent_itemsets['Feature Set'].iloc[index.row()]:
			list_item = self.feature_list.findItems(item,QtCore.Qt.MatchExactly)[0]
			list_item.setSelected(True)

	def get_selected_features(self):
		return self.feature_list.selectedItems()

class ItemsetsTableModel(QtCore.QAbstractTableModel):
	def __init__(self,parent=None):
		super(ItemsetsTableModel,self).__init__(parent=parent)
		self.frequent_itemsets = pd.DataFrame()
		self.items = []

	def rowCount(self, parent):
		return self.frequent_itemsets.shape[0]

	def columnCount(self, parent):
		return self.frequent_itemsets.shape[1]

	def data(self,index,role=QtCore.Qt.DisplayRole):
		if index.isValid():
			if role == QtCore.Qt.DisplayRole:
				i,j = index.row(),index.column()
				value = self.frequent_itemsets.iloc[i,j]
				if pd.isnull(value):
					return ''
				else:
					return str(value)
		return QtCore.QVariant()

	def headerData(self,section,orientation,role=QtCore.Qt.DisplayRole):
		if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
			return self.frequent_itemsets.columns[section]
		return QtCore.QAbstractTableModel.headerData(self,section,orientation,role)

	def sort(self,column,order=QtCore.Qt.AscendingOrder):
		self.layoutAboutToBeChanged.emit()
		if order == QtCore.Qt.AscendingOrder:
			self.frequent_itemsets.sort_values(by=self.frequent_itemsets.columns[column],ascending=True,inplace=True)
		elif order == QtCore.Qt.DescendingOrder:
			self.frequent_itemsets.sort_values(by=self.frequent_itemsets.columns[column],ascending=False,inplace=True)
		self.layoutChanged.emit()

	def update_frequent_itemsets(self,df,min_support=0.5):
		self.beginResetModel()
		dfisnull = ~pd.isnull(df)
		self.items = df.columns
		self.frequent_itemsets = apriori(dfisnull,use_colnames=True,min_support=0.5)
		self.frequent_itemsets.columns = ['Support','Feature Set']
		self.frequent_itemsets['# Features'] = self.frequent_itemsets['Feature Set'].apply(lambda x: len(x))
		self.frequent_itemsets['Feature Set'] = self.frequent_itemsets['Feature Set'].apply(lambda x: tuple(x))
		self.frequent_itemsets.sort_values(by='# Features',ascending=False)
		self.frequent_itemsets = self.frequent_itemsets[['Support','# Features','Feature Set']]
		self.endResetModel()



