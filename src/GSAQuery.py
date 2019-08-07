from __future__ import division
import pandas as pd
import sys, operator, os
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import cv2
from models import ResultsTableModel
from GSAImage import GSAImage
from GSAStats import TSNEWidget, PlotWidget
from gresq.csv2db2 import build_db
from gresq.database import sample, preparation_step, dal, Base, mdf_forge
from sqlalchemy import String, Integer, Float, Numeric
from gresq.config import config

"""
Each primary field will correspond to an MDF schema. Each of these are models 
(whose schema is in gresq/database.py) that are stored as separate datasets on MDF
so when a user selects a primary field, they are searching a particular group
of datasets on MDF.
	mdf_forge_fields:			mdf_forge schema. This corresponds to the raw data.
	raman_spectrum_fields:		raman_spectrum schema. This corresponds the Raman postprocessing (peaks, fwhm, etc.)
	sem_postprocess_fields		sem_postprocess schema. This corresponds to SEM postprocessing 
								like coverage, orientation, etc. The raw data may contain some
								of this information as well if the user inputs it during submission. 
								However, that information is stored in the mdf_forge model.
"""
mdf_forge_fields = [
	'title',
	'grain_size',
	'orientation',
	'catalyst',
	'base_pressure',
    'max_temperature',
    'carbon_source',
    'sample_surface_area',
	'sample_thickness'
]
raman_spectrum_fields = []

sem_postprocess_fields = []

results_fields = mdf_forge_fields+raman_spectrum_fields+sem_postprocess_fields

selection_list = {
	'Sample Fields': mdf_forge_fields,
	'Raman Analysis Fields': raman_spectrum_fields,
	'SEM Analysis Fields': sem_postprocess_fields
	}

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
	"""
	Main query widget.
	"""
	def __init__(self,parent=None):
		super(GSAQuery,self).__init__(parent=parent)
		self.filters = []
		self.filter_fields = QtGui.QStackedWidget()
		self.filter_fields.setMaximumHeight(50)
		self.filter_fields.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
		self.filters_dict = {}
		for field in mdf_forge_fields:
			widget = self.generate_field(model=mdf_forge,field=field)
			widget.setSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Preferred)
			self.filters_dict[getattr(mdf_forge,field).info['verbose_name']] = widget
			self.filter_fields.addWidget(widget)

		self.primary_selection = QtGui.QComboBox()
		self.primary_selection.addItems(sorted(selection_list.keys()))
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
		# self.results.setFixedHeight(300)

		self.preview = PreviewWidget()
		# self.results.plot.scatter_plot.sigClicked.connect(lambda x: self.preview.select(self.results.results_model,x[0]))

		self.addFilterBtn = QtGui.QPushButton('Add Filter')
		self.addFilterBtn.clicked.connect(lambda: self.addFilter(self.filter_fields.currentWidget()))

		# self.searchBtn = QtGui.QPushButton('Search')
		# self.searchBtn.clicked.connect(self.query)

		searchLabel = QtGui.QLabel('Query')
		searchLabel.setFont(label_font)

		# previewLabel = QtGui.QLabel('Preview')
		# previewLabel.setFont(label_font)

		resultsLabel = QtGui.QLabel('Results')
		resultsLabel.setFont(label_font)

		searchLayout = QtGui.QGridLayout() 
		searchLayout.setAlignment(QtCore.Qt.AlignTop)
		searchLayout.addWidget(self.primary_selection,1,0)
		searchLayout.addWidget(self.secondary_selection,2,0)
		searchLayout.addWidget(self.filter_fields,3,0)
		searchLayout.addWidget(self.addFilterBtn,4,0)
		searchLayout.addWidget(self.filter_table,5,0,4,1)

		resultsLayout = QtGui.QSplitter(QtCore.Qt.Vertical)
		# resultsLayout.setAlignment(QtCore.Qt.AlignTop)
		resultsLayout.addWidget(self.results)
		resultsLayout.addWidget(self.preview)

		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.layout.addWidget(searchLabel,0,0)
		self.layout.addLayout(searchLayout,1,0)
		self.layout.addWidget(resultsLabel,0,1)
		self.layout.addWidget(resultsLayout,1,1)
		
	
	def generate_field(self,model,field):
		"""
		Generates an input selected field of selected model.

		model:			sqlalchemy model to which the field corresponds
		field:			column within the sqlalchemy model
		"""
		cla = model
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
		"""
		Populates secondary selection combo box with fields corresponding to the primary selection model.
		"""
		selection_list = {
			'Sample Fields': {'fields':mdf_forge_fields,'model':mdf_forge},
			'Raman Analysis Fields': {'fields':raman_spectrum_fields,'model':None},
			'SEM Analysis Fields': {'fields':sem_postprocess_fields,'model':None}
			}

		self.secondary_selection.clear()
		self.secondary_selection.addItems([getattr(selection_list[selection]['model'],v).info['verbose_name'] for v in selection_list[selection]['fields']])

	def addFilter(self,widget):
		"""
		Adds filter to search query. Three actions take place:
			- A row is added to filter_table
			- A sqlalchemy filter object is appended to the filters list
			- A SQL query is performed using new filters list.
		"""
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
			self.query(self.filters)

	def deleteRow(self):
		"""
		Deletes filter associated with row in filter_table when delete button is activated. Three actions take place:
			- The row is deleted from filter_table
			- The corresponding sqlalchemy filter object is removed from the filters list
			- A SQL query is performed using new filters list. 
		"""
		row = self.filter_table.indexAt(self.sender().parent().pos()).row()
		if row >= 0:
			self.filter_table.removeRow(row)
			del self.filters[row]
			self.query(self.filters)

	def query(self,filters):
		"""
		Runs query on results widget. This is a separate function so as to make the selection signal work properly.
		This is because the model must be set before selection signalling can be connected.
		"""
		self.results.query(self.filters)
		self.results.results_table.selectionModel().currentChanged.connect(lambda x: self.preview.select(self.results.results_model,x))

class ValueFilter(QtGui.QWidget):
	"""
	Creates new filter input for numeric fields.

	model:			sqlalchemy model to which the field corresponds
	field:			column within the sqlalchemy model
	"""
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
	"""
	Creates new filter input for class (string) fields.

	model:			sqlalchemy model to which the field corresponds
	field:			column within the sqlalchemy model
	"""
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
	"""
	Widget for displaying data associated with selected sample. Contains tabs for:
		-Graphene details
		-SEM data (raw and postprocessed)
		-Raman data (raw and postprocessed)
		-Recipe visualization
		-Provenance information
	"""
	def __init__(self,parent=None):
		super(PreviewWidget,self).__init__(parent=parent)
		self.detail_tab = FieldsDisplayWidget(fields=mdf_forge_fields,model=mdf_forge)
		# self.provenance_tab = FieldsDisplayWidget()
		self.setTabPosition(QtGui.QTabWidget.South)

		self.addTab(self.detail_tab,'Details')
		self.addTab(QtGui.QWidget(),'SEM')
		self.addTab(QtGui.QWidget(),'Raman')
		self.addTab(QtGui.QWidget(),'Recipe')
		self.addTab(QtGui.QWidget(),'Provenance')

	def select(self,model,index):
		"""
		Select index from ResultsTableModel model.

		model:				ResultsTableModel object
		index:				Index from ResultsWidget table.
		"""
		self.detail_tab.setData(model,index)

class ResultsWidget(QtGui.QTabWidget):
	"""
	Widget for displaying results associated with a query. Contains tabs:
		- Results:				Each row associated with a sample and column corresponding to 
								a field. Clicking a row selects that sample for the PreviewWidget.
		- t-SNE:				Allows users to conduct t-SNE visualization on queried data.
		- Plot:					Allows users to scatter plot queried data.
	"""
	def __init__(self,parent=None):
		super(ResultsWidget,self).__init__(parent=parent)
		self.setTabPosition(QtGui.QTabWidget.North)
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
		"""
		Queries SQL database using list of sqlalchemy filters.

		filters:				list of sqlalchemy filters
		"""
		self.results_model = ResultsTableModel()
		if len(filters)>0:
			with dal.session_scope() as session:
				# q = session.query(sample).join(preparation_step,sample.preparation_steps).filter(*filters).distinct()
				q = session.query(mdf_forge).filter(*filters).distinct()
				self.results_model.read_sqlalchemy(q.statement,session)
		self.results_table.setModel(self.results_model)
		for c in range(self.results_model.columnCount(parent=None)):
			if self.results_model.df.columns[c] not in results_fields:
				self.results_table.hideColumn(c)
		self.results_table.resizeColumnsToContents()
		self.plot.setModel(self.results_model)
		self.tsne.setModel(self.results_model)

class FieldsDisplayWidget(QtGui.QScrollArea):
	"""
	Generic widget that creates a display from the selected fields from a particular model. 

	fields:	The fields from the model to generate the form. Note: fields must exist in the model.
	model:	The model to base the display on.
	"""
	def __init__(self,fields,model,elements_per_col=100,parent=None):
		super(FieldsDisplayWidget,self).__init__(parent=parent)
		self.contentWidget = QtGui.QWidget()
		self.layout = QtGui.QGridLayout(self.contentWidget)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.fields = {}

		for f,field in enumerate(fields):
			self.fields[field] = {}
			self.fields[field]['label'] = QtGui.QLabel(getattr(model,field).info['verbose_name'])
			self.fields[field]['label'].setWordWrap(True)
			# self.fields[field]['label'].setMaximumWidth(120)
			# self.fields[field]['label'].setMinimumHeight(self.fields[field]['label'].sizeHint().height())
			self.fields[field]['value'] = QtGui.QLabel()
			self.fields[field]['value'].setMinimumWidth(50)
			self.fields[field]['value'].setAlignment(QtCore.Qt.AlignRight)
			self.layout.addWidget(self.fields[field]['label'],f%elements_per_col,2*(f//elements_per_col))
			self.layout.addWidget(self.fields[field]['value'],f%elements_per_col,2*(f//elements_per_col)+1)

		self.setWidgetResizable(True)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setWidget(self.contentWidget)

	def setData(self,model,index):
		"""
		Update data displayed in the FieldsDisplayWidget for selected index in ResultsTableModel.

		model:				ResultsTableModel object
		index:				Index from ResultsWidget table.
		"""
		for field in self.fields.keys():
			if field in model.df.columns:
				value = model.df[field].iloc[index.row()]
				if pd.isnull(value):
					value = ''
				self.fields[field]['value'].setText(str(value))		

class SEMDisplayTab(QtGui.QScrollArea):
	def __init__(self,parent=None):
		super(SEMDisplayTab,self).__init__(parent=parent)
		self.contentWidget = QtGui.QWidget()
		self.layout = QtGui.QGridLayout(self.contentWidget)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		
		self.file_list = QtGui.QListWidget()
		self.sem_tabs = QtGui.QTabWidget()
		self.sem_info = QtGui.QStackedWidget()

		self.setWidgetResizable(True)
		self.setWidget(self.contentWidget)

	def update(self,sample_json=None,postprocess_json=None):
		if sample_model != None:
			for s,sem in enumerate(sample_model.sem_files,1):
				self.file_list.addItem("SEM Image %d"%s)
				image_tab = pg.GraphicsLayoutWidget()
				wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
				wImgItem = pg.ImageItem()
				wImgItem.setImage(fpath)
				wImgBox_VB.addItem(wImgItem)
				wImgBox_VB.setAspectLocked(True)

				self.sem_tabs.addTab(image_tab,"Raw Data")
				self.file_list.currentRowChanged.connect(self.sem_tabs.setCurrentIndex)


class RamanDisplayTab(QtGui.QScrollArea):
	def __init__(self,parent=None):
		super(RamanDisplayTab,self).__init__(parent=parent)
		self.contentWidget = QtGui.QWidget()
		self.layout = QtGui.QGridLayout(self.contentWidget)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.setWidgetResizable(True)
		self.setWidget(self.contentWidget)

	def update(self,sample_json=None):
		pass

if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)
	with dal.session_scope() as session:
		build_db(session,os.path.join(os.getcwd(),'../data'))
	app = QtGui.QApplication([])
	query = GSAQuery()
	query.show()
	sys.exit(app.exec_())
