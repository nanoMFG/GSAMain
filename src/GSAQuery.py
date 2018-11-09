from __future__ import division
import pandas as pd
import sys, operator, os
from PyQt5 import QtGui, QtCore
from models import ResultsTableModel
from GSAImage import GSAImage
from GSAStats import TSNEWidget, PlotWidget
from gresq.csv2db import build_db
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
    'carbon_source',
    'carbon_source_flow_rate'
]

results_fields = graphene_fields+conditions_fields

sql_validator = {
	'int': lambda x: isinstance(x.property.columns[0].type,Integer),
	'float': lambda x: isinstance(x.property.columns[0].type,Float),
	'str': lambda x: isinstance(x.property.columns[0].type,String)
}

operators = {
	'==': operator.eq,
	'!=': operator.ne,
	'<': operator.lt,
	'>': operator.gt,
	'<=': operator.le,
	'>=': operator.ge
}

label_font = QtGui.QFont("Helvetica", 28, QtGui.QFont.Bold) 

class GSAQuery(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GSAQuery,self).__init__(parent=parent)
		self.filters = []
		self.filter_fields = QtGui.QStackedWidget()
		self.filter_fields.setMaximumHeight(50)
		self.filter_fields.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
		self.filters_dict = {}
		for field in graphene_fields+conditions_fields:
			widget = self.generate_field(field)
			widget.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
			self.filters_dict[getattr(sample,field).info['verbose_name']] = widget
			self.filter_fields.addWidget(widget)
		for field in furnace_fields:
			widget = self.generate_field(field)
			widget.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
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
		self.filter_table.setColumnCount(4)
		self.filter_table.setHorizontalHeaderLabels(['Field','','Value',''])
		header = self.filter_table.horizontalHeader()       
		header.setSectionResizeMode(0, QtGui.QHeaderView.Stretch)
		self.filter_table.setColumnWidth(1,30)
		self.filter_table.setColumnWidth(2,100)
		self.filter_table.setColumnWidth(3,25)
		self.filter_table.setWordWrap(True)
		self.filter_table.verticalHeader().setVisible(False)

		self.results = ResultsWidget()
		self.results.setMinimumWidth(500)

		self.preview = PreviewWidget()
		self.results.results_table.activated.connect(lambda x: self.preview.select(self.results.results_model,x))
		# self.results.plot.scatter_plot.sigClicked.connect(lambda x: self.preview.select(self.results.results_model,x[0]))

		self.addFilterBtn = QtGui.QPushButton('Add Filter')
		self.addFilterBtn.clicked.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))

		# self.searchBtn = QtGui.QPushButton('Search')
		# self.searchBtn.clicked.connect(self.query)

		searchLabel = QtGui.QLabel('Query')
		searchLabel.setFont(label_font)

		previewLabel = QtGui.QLabel('Preview')
		previewLabel.setFont(label_font)

		resultsLabel = QtGui.QLabel('Results')
		resultsLabel.setFont(label_font)

		self.layout.addWidget(searchLabel,0,0,1,1)
		self.layout.addWidget(self.primary_selection,1,0,1,1)
		self.layout.addWidget(self.secondary_selection,2,0,1,1)
		self.layout.addWidget(self.filter_fields,3,0,1,1)
		self.layout.addWidget(self.addFilterBtn,4,0,1,1)
		self.layout.addWidget(self.filter_table,5,0,4,1)
		self.layout.addWidget(resultsLabel,0,1,1,1)
		self.layout.addWidget(self.results,1,1,8,1)
		self.layout.addWidget(previewLabel,0,2,1,1)
		self.layout.addWidget(self.preview,1,2,8,1)

	def generate_field(self,field):
		if field in graphene_fields or field in conditions_fields:
			cla = sample
		elif field in furnace_fields:
			cla = preparation_step
		if sql_validator['int'](getattr(cla,field)) == True:
			vf = ValueFilter(model=cla,field=field,validate=int)
			vf.input.returnPressed.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))
			return vf
		elif sql_validator['float'](getattr(cla,field)) == True:
			vf = ValueFilter(model=cla,field=field,validate=int)
			vf.input.returnPressed.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))
			return vf
		elif sql_validator['str'](getattr(cla,field)) == True:
			with dal.session_scope() as session:
				classes = []
				for v in session.query(getattr(cla,field)).distinct():
					classes.append(getattr(v,field))
			return ClassFilter(model=cla,field=field,classes=classes,validate=str)
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

	def addFilter(self,widget):
		if widget.valid():
			self.filters.append(widget.sqlalchemy_filter())
			row = self.filter_table.rowCount()
			self.filter_table.insertRow(row)
			self.filter_table.setItem(row,0,QtGui.QTableWidgetItem(widget.label.text()))
			self.filter_table.setItem(row,1,QtGui.QTableWidgetItem(widget.operation))
			self.filter_table.setItem(row,2,QtGui.QTableWidgetItem(str(widget.value)))
			# self.filter_table.resizeRowsToContents()

			delRowBtn = QtGui.QPushButton('X')
			delRowBtn.clicked.connect(self.deleteRow)
			self.filter_table.setCellWidget(row,3,delRowBtn)
			widget.clear()
			self.results.query(self.filters)

	def deleteRow(self):
		row = self.filter_table.indexAt(self.sender().parent().pos()).row()
		if row >= 0:
			self.filter_table.removeRow(row)
			del self.filters[row]
			self.results.query(self.filters)

class ValueFilter(QtGui.QWidget):
	def __init__(self,model,field,validate=None,parent=None):
		super(ValueFilter,self).__init__(parent=parent)
		self.field = field
		self.model = model
		self.validate = validate

		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel(getattr(model,field).info['verbose_name'])
		# self.label.setFixedWidth(150)
		self.label.setWordWrap(True)
		self.comparator = QtGui.QComboBox()
		self.comparator.setFixedWidth(50)
		self.comparator.addItems(sorted(list(operators)))
		self.input = QtGui.QLineEdit()
		self.input.setFixedWidth(100)

		if self.validate == int:
			self.input.setValidator(QtGui.QIntValidator())
		elif self.validate == float:
			self.input.setValidator(QtGui.QDoubleValidator())

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.comparator,0,1)
		layout.addWidget(self.input,0,2)

	@property
	def operation(self):
		return self.comparator.currentText()

	@property
	def value(self):
		return self.validate(self.input.text())

	def valid(self):
		try:
			self.value
			return True
		except:
			return False

	def sqlalchemy_filter(self):
		return operators[self.comparator.currentText()](getattr(self.model,self.field),self.value)

	def clear(self):
		self.input.clear()

class ClassFilter(QtGui.QWidget):
	def __init__(self,model,field,validate=None,classes=[],parent=None):
		super(ClassFilter,self).__init__(parent=parent)
		self.field = field
		self.model = model
		self.validate = validate

		layout = QtGui.QGridLayout(self)
		self.label = QtGui.QLabel(getattr(model,field).info['verbose_name'])
		# self.label.setFixedWidth(150)
		self.label.setWordWrap(True)
		self.classes = QtGui.QComboBox()
		self.classes.addItems(classes)

		layout.addWidget(self.label,0,0)
		layout.addWidget(self.classes,0,1)

	@property
	def operation(self):
		return 'AND'

	@property
	def value(self):
		assert self.classes.count() > 0
		return self.validate(self.classes.currentText())

	def valid(self):
		try:
			self.value
			return True
		except:
			return False

	def sqlalchemy_filter(self):
		return operator.eq(getattr(self.model,self.field),self.value)

	def clear(self):
		pass

class PreviewWidget(QtGui.QTabWidget):
	def __init__(self,parent=None):
		super(PreviewWidget,self).__init__(parent=parent)
		self.detail_tab = GrapheneWidget()
		self.setTabPosition(QtGui.QTabWidget.South)

		self.addTab(self.detail_tab,'Details')
		self.addTab(QtGui.QWidget(),'SEM')
		self.addTab(QtGui.QWidget(),'Raman')
		self.addTab(QtGui.QWidget(),'Recipe')

	def select(self,model,index):
		self.detail_tab.setData(model,index)

class GrapheneWidget(QtGui.QWidget):
	def __init__(self,parent=None):
		super(GrapheneWidget,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.fields = {}

		elements_per_row = 30
		for f,field in enumerate(graphene_fields):
			self.fields[field] = {}
			self.fields[field]['label'] = QtGui.QLabel(getattr(sample,field).info['verbose_name'])
			self.fields[field]['label'].setWordWrap(True)
			self.fields[field]['label'].setMinimumWidth(120)
			self.fields[field]['value'] = QtGui.QLabel()
			self.fields[field]['value'].setMinimumWidth(50)
			self.fields[field]['value'].setAlignment(QtCore.Qt.AlignRight)
			self.layout.addWidget(self.fields[field]['label'],f%elements_per_row,2*(f//elements_per_row))
			self.layout.addWidget(self.fields[field]['value'],f%elements_per_row,2*(f//elements_per_row)+1)

	def setData(self,model,index):
		for field in graphene_fields:
			value = model.df[field].iloc[index.row()]
			if pd.isnull(value):
				value = ''
			self.fields[field]['value'].setText(str(value))

class ResultsWidget(QtGui.QTabWidget):
	def __init__(self,parent=None):
		super(ResultsWidget,self).__init__(parent=parent)
		self.setTabPosition(QtGui.QTabWidget.South)
		self.results_model = ResultsTableModel()
		self.results_table = QtGui.QTableView()
		self.results_table.setMinimumWidth(400)
		self.results_table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.results_table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.results_table.setSortingEnabled(True)

		self.tsne = TSNEWidget()
		self.plot = PlotWidget()

		self.addTab(self.results_table,'Query Results')
		self.addTab(self.plot,'Plotting')
		self.addTab(self.tsne,'t-SNE')

	def query(self,filters):
		self.results_model = ResultsTableModel()
		if len(filters)>0:
			with dal.session_scope() as session:
				q = session.query(sample).join(preparation_step,sample.preparation_steps).filter(*filters).distinct()
				self.results_model.read_sqlalchemy(q.statement,session)
		self.results_table.setModel(self.results_model)
		for c in range(self.results_model.columnCount(parent=None)):
			if self.results_model.df.columns[c] not in results_fields:
				self.results_table.hideColumn(c)
		self.results_table.resizeColumnsToContents()
		self.plot.setModel(self.results_model)
		self.tsne.setModel(self.results_model)

if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)
	with dal.session_scope() as session:
		build_db(session,os.path.join(os.getcwd(),'data'))
	app = QtGui.QApplication([])
	query = GSAQuery()
	query.show()
	sys.exit(app.exec_())
