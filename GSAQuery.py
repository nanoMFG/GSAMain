from __future__ import division
import numpy as np
import scipy as sc
import sys
from PyQt5 import QtGui, QtCore
from GSAImage import GSAImage

class GSAQuery:
	def __init__(self):
		self.main = QtGui.QWidget()
		self.filters = []
		self.layout = QtGui.QGridLayout()
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.layout.addWidget(FilterWidget(),0,0)

		self.main.setLayout(self.layout)

	def widget(self):
		return self.main

	def run(self):
		self.main.show()

class FilterWidget(QtGui.QWidget):
	def __init__(self,parent=None):
		super(FilterWidget,self).__init__(parent=parent)
		layout = QtGui.QGridLayout(self)

		self.criteria = [
			'furnace_temperature',
			'furnace_pressure',
			'catalyst'
		]

		self.widgets = {}

		for c,cr in enumerate(self.criteria):
			row = FilterRow()
			row.label.setText(cr)
			layout.addWidget(row,c,0)
			self.widgets[cr] = row

	def getFilters(self):
		filters = {}
		for widget in self.widgets:
			filters[widget.label.text()] = 

class FilterRow(QtGui.QWidget):
	def __init__(self,parent=None):
		super(FilterRow,self).__init__(parent=parent)
		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel()
		self.label.setFixedWidth(150)
		self.comparator = QtGui.QComboBox()
		self.comparator.addItems(['=','!=','<','<=','>','>='])
		self.input = QtGui.QLineEdit()
		self.input.setFixedWidth(100)

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.comparator,0,1)
		layout.addWidget(self.input,0,2)


if __name__ == '__main__':
	app = QtGui.QApplication([])
	query = GSAQuery()
	query.run()
	sys.exit(app.exec_())
