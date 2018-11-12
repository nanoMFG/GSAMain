from PyQt5 import QtGui, QtCore
import pandas as pd
from mlxtend.frequent_patterns import apriori

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
		self.frequent_itemsets['Support'] = self.frequent_itemsets['Support'].apply(lambda x: round(x,4))
		self.frequent_itemsets.sort_values(by='# Features',ascending=False,inplace=True)
		self.frequent_itemsets = self.frequent_itemsets[['Support','# Features','Feature Set']]
		self.endResetModel()

class ResultsTableModel(QtCore.QAbstractTableModel):
	def __init__(self,parent=None):
		super(ResultsTableModel,self).__init__(parent=parent)
		self.df = pd.DataFrame()

	def read_sqlalchemy(self,statement,session):
		self.beginResetModel()
		self.df = pd.read_sql_query(statement,session.connection())
		self.endResetModel()

	def rowCount(self, parent):
		return self.df.shape[0]

	def columnCount(self, parent):
		return self.df.shape[1]

	def data(self,index,role=QtCore.Qt.DisplayRole):
		if index.isValid():
			if role == QtCore.Qt.DisplayRole:
				i,j = index.row(),index.column()
				value = self.df.iloc[i,j]
				if pd.isnull(value):
					return ''
				else:
					return str(value)
		return QtCore.QVariant()

	def headerData(self,section,orientation,role=QtCore.Qt.DisplayRole):
		if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
			return self.df.columns[section]
		return QtCore.QAbstractTableModel.headerData(self,section,orientation,role)

	def sort(self,column,order=QtCore.Qt.AscendingOrder):
		self.layoutAboutToBeChanged.emit()
		if order == QtCore.Qt.AscendingOrder:
			self.df = self.df.sort_values(by=self.df.columns[column],ascending=True)
		elif order == QtCore.Qt.DescendingOrder:
			self.df = self.df.sort_values(by=self.df.columns[column],ascending=False)
		self.layoutChanged.emit()


