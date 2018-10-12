from __future__ import division
import numpy as np
import scipy as sc
import sys
from GSAImage import GSAImage

class GSAQuery:
	def __init__(self):
		self.main = QtGui.QWidget()
		self.filters = []
		self.layout = QtGui.QGridLayout()
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.searchOptions = QtGui.QStackedWidget()
		self.searchOptions.setFixedWidth(300)
		self.criteria = {
			'Furnace Criteria': FurnaceCriterion(),
			'Flow Criteria': FlowCriterion()
		}
		self.criteriaBox = QtGui.QComboBox()
		for c in self.criteria.keys():
			self.criteriaBox.addItem(c)
			self.searchOptions.addWidget(self.criteria[c].widget())

		self.filterList = QtGui.QListWidget()
		self.resultsList = QtGui.QListWidget() # Use Table Widget
		self.addFilterBtn = QtGui.QPushButton('Add Filter')
		self.searchBtn = QtGui.QPushButton('Search')
		self.imagePreview =  pg.LayoutWidget()
		with open('temp_1538149879.json','r') as f:
			d = json.load(f)
		self.imagePreview.addWidget(ImageAnalyzer.viewOnlyWidget(d),0,0)
		self.imagePreview.setFixedHeight(300)

		self.addFilterBtn.clicked.connect(lambda: self.addFilter())
		self.criteriaBox.currentIndexChanged.connect(self.searchOptions.setCurrentIndex)

		self.layout.addWidget(self.criteriaBox,0,0)
		self.layout.addWidget(self.searchOptions,1,0)
		self.layout.addWidget(self.addFilterBtn,2,0)
		self.layout.addWidget(self.filterList,3,0)
		self.layout.addWidget(self.searchBtn,4,0)
		self.layout.addWidget(self.imagePreview,0,1,2,2)
		self.layout.addWidget(self.resultsList,2,1,3,2)
		self.main.setLayout(self.layout)

	def addFilter(self):
		key = self.criteriaBox.currentText()
		self.filterList.addItem("%d %s"%(self.filterList.count(),key))
		self.filters.append(self.criteria[key].getValues())
		self.criteria[key].clear()

		print(self.filters)

	def widget(self):
		return self.main

class Criterion:
	def __init__(self):
		self.main = QtGui.QWidget()
		self.layout = QtGui.QGridLayout()
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.fields = {}
		self.values = {}

	def widget(self):
		return self.main

	def clear(self):
		pass

class FurnaceCriterion(Criterion):
	def __init__(self):
		super(FurnaceCriterion,self).__init__()
		self.criteria = ['Furnace Criterion %d'%i for i in range(5)]
		
		for i,c in enumerate(self.criteria):
			self.fields[c] = QtGui.QLineEdit()
			self.values[c] = None
			self.fields[c].setPlaceholderText('Example Text %d'%i)
			self.layout.addWidget(QtGui.QLabel(c),i,0)
			self.layout.addWidget(self.fields[c],i,1)

		self.main.setLayout(self.layout)

	def getValues(self):
		for field in self.fields.keys():
			self.values[field] = self.fields[field].text()
		return self.values

class FlowCriterion(Criterion):
	def __init__(self):
		super(FlowCriterion,self).__init__()
		self.criteria = ['Flow Criterion %d'%i for i in range(5)]
		
		for i,c in enumerate(self.criteria):
			self.fields[c] = QtGui.QLineEdit()
			self.values[c] = None
			self.fields[c].setPlaceholderText('Example Text %d'%i)
			self.layout.addWidget(QtGui.QLabel(c),i,0)
			self.layout.addWidget(self.fields[c],i,1)

		self.main.setLayout(self.layout)

	def getValues(self):
		for field in self.fields.keys():
			self.values[field] = self.fields[field].text()
		return self.values







