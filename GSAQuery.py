from __future__ import division
import numpy as np
import scipy as sc
import sys
from PyQt5 import QtGui, QtCore
from GSAImage import GSAImage
from gresq.database import sample, preparation_step, dal, Base
from gresq.config import config

graphene_fields = [
	'average_thickness_of_growth',
	'standard_deviation_of_growth',
	'number_of_layers',
	'growth_coverage',
	'domain_size',
	'geometry', # what is this
	'silicon_peak_shift',
	'silicon_peak_amplitude',
	'silicon_fwhm',
	'd_peak_shift',
	'd_peak_amplitude',
	'd_fwhm',
	'g_peak_shift',
	'g_peak_amplitude',
	'g_fwhm',
	'g_prime_peak_shift',
	'g_prime_peak_amplitude',
	'g_prime_fwhm',
	'lorenztians_under_g_prime_peak',
	'sample_surface_area',
]

conditions_fields = [
	'thickness',
	'diameter',
	'length',
	'catalyst',
	'tube_diameter',
	'cross_sectional_area',
	'tube_length',
	'base_pressure'
]

furnace_fields = [
    'name',
    'furnace_temperature',
    'furnace_pressure',
    'carbon_source'
]

class GSAQuery(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAQuery,self).__init__(parent=parent)
		self.filters = QtGui.QStackedWidget()
		self.filters_dict = {}
		for field in graphene_fields:
			widget = self.generate_field(field)
			self.filters_dict[field] = widget
			self.filters.addWidget(widget)

		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.primary_selection = QtGui.QComboBox()
		self.primary_selection.addItems(['Growth Conditions','Furnace Conditions','Graphene Characteristics'])
		self.primary_selection.activated[str].connect(self.populate_secondary)

		self.secondary_selection = QtGui.QComboBox()
		self.secondary_selection.activated[str].connect()

		self.searchBtn = QtGui.QPushButton('Search')
		self.searchBtn.clicked.connect(self.search)

		self.layout.addWidget(self.searchBtn,1,0)

	def generate_field(self,field):
		if field in graphene_fields or field in conditions_fields:
			cla = sample
		elif  field in furnace_fields:
			cla = preparation_step

	def populate_secondary(self,selection):
		selection_list = {
			'Growth Conditions': conditions_fields,
			'Furnace Conditions': furnace_fields,
			'Graphene Characteristics': graphene_fields
			}
		self.secondary_selection.clear()
		self.secondary_selection.addItems(selection_list[selection])

	def search(self):
		print(self.filterFields.getFilters())

	def run(self):
		self.show()

class ValueFilter(QtGui.QWidget):
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

class ClassFilter(QtGui.QWidget):
	def __init__(self,parent=None):
		super(FilterRow,self).__init__(parent=parent)
		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel()
		self.label.setFixedWidth(150)
		self.classes = QtGui.QComboBox()

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.self.classes,0,1)

if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)
	app = QtGui.QApplication([])
	query = GSAQuery()
	query.run()
	sys.exit(app.exec_())
