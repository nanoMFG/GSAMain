from __future__ import division
import numpy as np
import scipy as sc
import sys
from PyQt5 import QtGui, QtCore
from GSAImage import GSAImage
from gresq.database import sample, preparation_step, dal, Base
from sqlalchemy import String, Integer, Float, Numeric
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

sql_validator = {
	'int': lambda x: isinstance(x.property.columns[0].type,Integer),
	'float': lambda x: isinstance(x.property.columns[0].type,Float),
	'str': lambda x: isinstance(x.property.columns[0].type,String)
}

class GSAQuery(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAQuery,self).__init__(parent=parent)
		self.filters = QtGui.QStackedWidget()
		self.filters_dict = {}
		for field in graphene_fields+conditions_fields:
			widget = self.generate_field(field)
			self.filters_dict[getattr(sample,field).info['verbose_name']] = widget
			self.filter_fields.addWidget(widget)
		for field in furnace_fields:
			widget = self.generate_field(field)
			self.filters_dict[getattr(preparation_step,field).info['verbose_name']] = widget
			self.filter_fields.addWidget(widget)

		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.primary_selection = QtGui.QComboBox()
		self.primary_selection.addItems(['Growth Conditions','Furnace Conditions','Graphene Characteristics'])
		self.primary_selection.activated[str].connect(self.populate_secondary)

		self.secondary_selection = QtGui.QComboBox()
		self.secondary_selection.activated[str].connect(lambda x: self.filter_fields.setCurrentWidget(self.filters_dict[x]))

		self.filter_table = QtGui.QTableWidget()

		self.addFilterBtn = QtGui.QPushButton('Add Filter')
		self.addFilterBtn.clicked.connect(lambda: self.search(self.filter_fields.currentWidget()))


		self.layout.addWidget(self.primary_selection,0,0)
		self.layout.addWidget(self.secondary_selection,0,1)
		self.layout.addWidget(self.filters,1,0,1,2)
		self.layout.addWidget(self.searchBtn,2,0,1,2)
		self.layout.addWidget(self.filter_table,3,0,1,2)

	def generate_field(self,field):
		if field in graphene_fields or field in conditions_fields:
			cla = sample
		elif field in furnace_fields:
			cla = preparation_step
		if sql_validator['int'](getattr(cla,field)) == True:
			return ValueFilter(validate='int',label=getattr(cla,field).info['verbose_name'])
		elif sql_validator['float'](getattr(cla,field)) == True:
			return ValueFilter(validate='float',label=getattr(cla,field).info['verbose_name'])
		elif sql_validator['str'](getattr(cla,field)) == True:
			with dal.session_scope() as session:
				classes = []
				for v in session.query(getattr(cla,field)).distinct():
					classes.append(getattr(v,field))
			return ClassFilter(classes=classes,label=getattr(cla,field).info['verbose_name'])
		else:
			raise ValueError('Field %s data type (%s) not recognized.'%(field,getattr(cla,field).property.columns[0].type))


	def populate_secondary(self,selection):
		selection_list = {
			'Growth Conditions': conditions_fields,
			'Furnace Conditions': furnace_fields,
			'Graphene Characteristics': graphene_fields
			}
		if selection == 'Growth Conditions' or selection == 'Graphene Characteristics':
			cla = sample
		elif selection == 'Furnace Conditions':
			cla = preparation_step
		self.secondary_selection.clear()
		self.secondary_selection.addItems([getattr(cla,v).info['verbose_name'] for v in selection_list[selection]])

	def search(self,widget):
		

class ValueFilter(QtGui.QWidget):
	def __init__(self,label,validate=None,parent=None):
		super(ValueFilter,self).__init__(parent=parent)
		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel(label)
		self.label.setFixedWidth(150)
		self.label.setWordWrap(True)
		self.comparator = QtGui.QComboBox()
		self.comparator.addItems(['=','!=','<','<=','>','>='])
		self.input = QtGui.QLineEdit()
		self.input.setFixedWidth(100)
		if validate == 'int':
			self.input.setValidator(QtGui.QIntValidator())
		elif validate == 'float':
			self.input.setValidator(QtGui.QDoubleValidator())

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.comparator,0,1)
		layout.addWidget(self.input,0,2)

class ClassFilter(QtGui.QWidget):
	def __init__(self,label,classes=[],parent=None):
		super(ClassFilter,self).__init__(parent=parent)
		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel(label)
		self.label.setFixedWidth(150)
		self.label.setWordWrap(True)
		self.classes = QtGui.QComboBox()
		self.classes.addItems(classes)

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.classes,0,1)

if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)
	app = QtGui.QApplication([])
	query = GSAQuery()
	query.show()
	sys.exit(app.exec_())
