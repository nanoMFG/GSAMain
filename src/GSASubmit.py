from __future__ import division
import numpy as np
import cv2, sys, time, json, copy, subprocess, os
from PyQt5 import QtGui, QtCore

from box_adaptor import BoxAdaptor
from gresq.database import sample, preparation_step, dal, Base, mdf_forge, author, raman_spectrum, recipe, properties, sem_file, raman_file, raman_set
from sqlalchemy import String, Integer, Float, Numeric, Date
from gresq.config import config
from gresq.csv2db import build_db
import GSARaman
from gresq.recipe import Recipe
from mdf_adaptor import MDFAdaptor, MDFException


sample_fields = [
	"material_name",
	"experiment_date"
]

preparation_fields = [
	'name',
	'duration',
	'furnace_temperature',
	'furnace_pressure',
	'sample_location',
	'helium_flow_rate',
	'hydrogen_flow_rate',
	'argon_flow_rate',
	'carbon_source',
	'carbon_source_flow_rate',
	'cooling_rate'
]

recipe_fields = [
	"catalyst",
	"tube_diameter",
	"cross_sectional_area",
	"tube_length",
	"base_pressure",
	"thickness",
	"diameter",
	"length"
]

properties_fields = [
	"average_thickness_of_growth",
	"standard_deviation_of_growth",
	"number_of_layers",
	"growth_coverage",
	"domain_size",
	"shape"
]

author_fields = ["first_name","last_name","institution"]

sql_validator = {
	'int': lambda x: isinstance(x.property.columns[0].type,Integer),
	'float': lambda x: isinstance(x.property.columns[0].type,Float),
	'str': lambda x: isinstance(x.property.columns[0].type,String),
	'date': lambda x: isinstance(x.property.columns[0].type,Date)
}

label_font = QtGui.QFont("Helvetica", 28, QtGui.QFont.Bold)
sublabel_font = QtGui.QFont("Helvetica", 18)

class GSASubmit(QtGui.QTabWidget):
	"""
	Main submission widget
	mode:				Upload method (local or nanohub)
	box_config_path:	Path to box configuration file
	"""
	def __init__(self,mode='local',parent=None, box_config_path=None):
		super(GSASubmit,self).__init__(parent=parent)
		self.mode = mode
		self.properties = PropertiesTab()
		self.preparation = PreparationTab()
		self.provenance = ProvenanceTab()
		self.file_upload = FileUploadTab(mode=self.mode)
		self.review = ReviewTab(box_config_path=box_config_path)

		self.setTabPosition(QtGui.QTabWidget.South)
		self.addTab(self.preparation,'Preparation')
		self.addTab(self.properties,'Properties')
		self.addTab(self.file_upload,'File Upload')
		self.addTab(self.provenance,"Provenance")
		self.addTab(self.review, 'Review')

		self.currentChanged.connect(lambda x: self.review.refresh(
			properties_response = self.properties.getResponse(),
			preparation_response = self.preparation.getResponse(),
			files_response = self.file_upload.getResponse(),
			provenance_response = self.provenance.getResponse()) if x == self.indexOf(self.review) else None,
		)

		self.review.submitButton.clicked.connect(lambda: self.review.submit(self.review.getFullResponse(
			properties_response = self.properties.getResponse(),
			preparation_response = self.preparation.getResponse(),
			files_response = self.file_upload.getResponse(),
			provenance_response = self.provenance.getResponse()
			)))

		self.provenance.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.review))
		self.preparation.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.properties))
		self.properties.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.file_upload))
		self.file_upload.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.provenance))

	def test(self):
		self.properties.testFill()
		self.provenance.testFill()
		self.preparation.testFill()

class FieldsFormWidget(QtGui.QWidget):
	"""
	Generic widget that creates a form from the selected fields from a particular model. Automatically
	determines whether to use a combo box or line edit widget. Applies appropriate validators and 
	allows users to select the appropriate unit as defined in the model. If the field is a String 
	field and 'choices' is not in the model 'info' dictionary, a line edit is used instead of combo box.

	fields:	The fields from the model to generate the form. Note: fields must exist in the model.
	model:	The model to base the form on. The model is used to determine data type of each field
			and appropriate ancillary information found in the field's 'info' dictionary.
	"""
	def __init__(self,fields,model,parent=None):
		super(FieldsFormWidget,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.fields = fields
		self.model = model
		
		self.input_widgets = {}
		self.other_input = {}
		self.units_input = {}

		for f,field in enumerate(fields):
			row = f%9
			col = f//9
			info = getattr(model,field).info
			self.layout.addWidget(QtGui.QLabel(info['verbose_name']),row,3*col)
			if sql_validator['str'](getattr(model,field)):
				input_set = []
				with dal.session_scope() as session:
					if hasattr(mdf_forge,field):
						for v in session.query(getattr(mdf_forge,field)).distinct():
							if getattr(v,field) not in input_set:
								input_set.append(getattr(v,field))
				if 'choices' in info.keys():	
					input_set.extend(info['choices'])
					self.input_widgets[field] = QtGui.QComboBox()
					self.input_widgets[field].addItems(input_set)
					self.input_widgets[field].addItem('Other')

					self.other_input[field] = QtGui.QLineEdit()
					self.other_input[field].setPlaceholderText('Enter other input here.')
					self.other_input[field].setFixedHeight(self.other_input[field].sizeHint().height())
					self.other_input[field].hide()
					
					self.input_widgets[field].activated[str].connect(
						lambda x, other_input = self.other_input[field]: other_input.show() if x == 'Other' else other_input.hide())
					self.layout.addWidget(self.other_input[field],row,3*col+2)
					self.input_widgets[field].activated[str].emit(self.input_widgets[field].currentText())

				else:
					self.input_widgets[field] = QtGui.QLineEdit()
				self.layout.addWidget(self.input_widgets[field],row,3*col+1)	

			elif sql_validator['date'](getattr(model,field)):
				self.input_widgets[field] = QtGui.QDateEdit()
				self.input_widgets[field].setCalendarPopup(True)
				self.input_widgets[field].setDate(QtCore.QDate.currentDate())
				self.layout.addWidget(self.input_widgets[field],row,3*col+1)

			else:
				self.input_widgets[field] = QtGui.QLineEdit()
				if sql_validator['int'](getattr(model,field)):
					self.input_widgets[field].setValidator(QtGui.QIntValidator())
				elif sql_validator['float'](getattr(model,field)):
					self.input_widgets[field].setValidator(QtGui.QDoubleValidator())
				
				if 'conversions' in info.keys():
					self.units_input[field] = QtGui.QComboBox()
					self.units_input[field].addItems(info['conversions'])					

				self.layout.addWidget(self.input_widgets[field],row,3*col+1)
				if field in self.units_input.keys():
					self.layout.addWidget(self.units_input[field],row,3*col+2)

	def getResponse(self):
		"""
		Returns a dictionary response of the form fields. Dictionary, D, is defined as:
			D[field] = {
				'value':	output of the input widget for 'field'. If empty, it is None.
				'unit':		output of the units widget for 'field'. If empty or nonexistent, it is None.
			}
		"""
		response = {}
		for field in self.fields:
			info = getattr(self.model,field).info
			response[field] = {}
			if isinstance(self.input_widgets[field],QtGui.QComboBox):
				if self.input_widgets[field].currentText() == 'Other':
					response[field]['value'] = self.other_input[field].text()
				else:
					response[field]['value'] = self.input_widgets[field].currentText()
				response[field]['unit'] = ''
			elif isinstance(self.input_widgets[field],QtGui.QDateTimeEdit):
				response[field]['value'] = self.input_widgets[field].date().toPyDate()
			else:
				response[field]['value'] = self.input_widgets[field].text() if self.input_widgets[field].text() != '' else None
				if field in self.units_input.keys():
					response[field]['unit'] = self.units_input[field].currentText()
				else:
					response[field]['unit'] = ''

		return response

	def fillResponse(self,response_dict):
		for field in self.fields:
			if response_dict[field]['value']:
				value = response_dict[field]['value']
				unit = response_dict[field]['unit']
				input_widget = self.input_widgets[field]
				if isinstance(self.input_widgets[field],QtGui.QComboBox):
					item_list = [input_widget.itemText(i) for i in range(input_widget.count())]
					if value in item_list:
						input_widget.setCurrentIndex(item_list.index(value))
					else:
						input_widget.setCurrentIndex(item_list.index("Other"))
						self.other_input[field].setText(value)
				elif isinstance(self.input_widgets[field],QtGui.QDateTimeEdit):
					date = QtCore.QDate(value[0],value[1],value[2])
					self.input_widgets[field].setDate(date)
				else:
					input_widget.setText(str(value))
					if field in self.units_input.keys():
						units_widget = self.units_input[field]
						units_list = [units_widget.itemText(i) for i in range(units_widget.count())]
						units_widget.setCurrentIndex(units_list.index(unit))

	def testFill(self,fields=None):
		response_dict = {}
		if fields == None:
			fields = self.fields
		for field in fields:
			response_dict[field] = {}
			response_dict[field]['value'] = random_fill(field,self.model)
			if 'std_unit' in getattr(self.model,field).info.keys():
				response_dict[field]['unit'] = getattr(self.model,field).info['std_unit']
			else:
				response_dict[field]['unit'] = None

		self.fillResponse(response_dict)


	def clear(self):
		for widget in list(self.input_widgets.values())+list(self.other_input.values()):
			if isinstance(widget,QtGui.QComboBox):
				widget.setCurrentIndex(0)
			elif isinstance(widget,QtGui.QLineEdit):
				widget.setText('')
			elif isinstance(widget,QtGui.QDateTimeEdit):
				widget.setDate(QtCore.QDate.currentDate())

class ProvenanceTab(QtGui.QWidget):
	"""
	Provenance information tab. Users input author information.
	"""
	def __init__(self,parent=None):
		super(ProvenanceTab,self).__init__(parent=parent)
		self.mainLayout = QtGui.QGridLayout(self)
		self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

		self.stackedFormWidget = QtGui.QStackedWidget()
		self.stackedFormWidget.setFrameStyle(QtGui.QFrame.StyledPanel)
		self.sample_input = FieldsFormWidget(fields=sample_fields,model=sample)
		self.author_list = QtGui.QListWidget()
		self.author_list.currentRowChanged.connect(self.stackedFormWidget.setCurrentIndex)
		self.add_author_btn = QtGui.QPushButton("New Author")
		self.remove_author_btn = QtGui.QPushButton("Remove Author")
		self.nextButton = QtGui.QPushButton('Next >>>')
		self.clearButton = QtGui.QPushButton('Clear Fields')
		spacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding)
		hspacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding,
			hPolicy = QtGui.QSizePolicy.Expanding)

		self.layout = QtGui.QGridLayout()
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.layout.addWidget(self.sample_input,0,0,1,2)
		self.layout.addWidget(self.stackedFormWidget,1,0,1,2)
		self.layout.addWidget(self.add_author_btn,2,0,1,1)
		self.layout.addWidget(self.remove_author_btn,2,1,1,1)
		self.layout.addWidget(self.author_list,3,0,1,2)
		self.layout.addItem(spacer,5,0)
		self.layout.addWidget(self.clearButton,4,0,1,2)
		self.mainLayout.addLayout(self.layout,0,0)
		self.mainLayout.addItem(hspacer,0,1)
		self.mainLayout.addWidget(self.nextButton,1,0,1,2)

		self.add_author_btn.clicked.connect(self.addAuthor)
		self.remove_author_btn.clicked.connect(self.removeAuthor)
		self.clearButton.clicked.connect(self.clear)

	def addAuthor(self):
		"""
		Add another author. Adds new entry to author list and creates new author input widget.
		"""
		w = FieldsFormWidget(fields=["first_name","last_name","institution"],model=author)
		idx = self.stackedFormWidget.addWidget(w)
		self.stackedFormWidget.setCurrentIndex(idx)
		self.author_list.addItem("%s, %s"%(w.input_widgets["last_name"].text(),w.input_widgets["first_name"].text()))
		item = self.author_list.item(idx)
		w.input_widgets['last_name'].textChanged.connect(
			lambda txt: item.setText("%s, %s"%(w.input_widgets["last_name"].text(),w.input_widgets["first_name"].text())))
		w.input_widgets['first_name'].textChanged.connect(
			lambda txt: item.setText("%s, %s"%(w.input_widgets["last_name"].text(),w.input_widgets["first_name"].text())))

	def removeAuthor(self):
		"""
		Removes author as selected from author list widget.
		"""
		x=self.author_list.currentRow()
		self.stackedFormWidget.removeWidget(self.stackedFormWidget.widget(x))
		self.author_list.takeItem(x)

	def getResponse(self):
		"""
		Returns a list of dictionary responses, as defined in FieldsFormWidget.getResponse() for each step.
		"""
		response = []
		for i in range(self.stackedFormWidget.count()):
			response.append(self.stackedFormWidget.widget(i).getResponse())
		return {'author':response, 'sample': self.sample_input.getResponse()}

	def clear(self):
		while self.author_list.count()>0:
			self.author_list.setCurrentRow(0)
			self.removeAuthor()
		self.sample_input.clear()

	def testFill(self):
		for _ in range(3):
			self.addAuthor()
			self.stackedFormWidget.currentWidget().testFill()

class PropertiesTab(QtGui.QWidget):
	"""
	Properties tab widget. Users input graphene properties and experimental parameters.
	"""
	def __init__(self,parent=None):
		super(PropertiesTab,self).__init__(parent=parent)
		self.mainLayout = QtGui.QGridLayout(self)
		self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

		self.properties_form = FieldsFormWidget(properties_fields,properties)
		self.nextButton = QtGui.QPushButton('Next >>>')
		self.clearButton = QtGui.QPushButton('Clear Fields')
		spacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding)
		hspacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding,
			hPolicy = QtGui.QSizePolicy.Expanding)

		self.layout = QtGui.QGridLayout()
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.layout.addWidget(self.properties_form,0,0)
		self.layout.addWidget(QtGui.QLabel("NOTE:\nThis section optional. Please input any properties data you may have."),2,0)
		self.layout.addWidget(self.clearButton,1,0)
		self.layout.addItem(spacer,3,0)

		self.mainLayout.addLayout(self.layout,0,0)
		self.mainLayout.addItem(hspacer,0,1)
		self.mainLayout.addWidget(self.nextButton,1,0,1,2)

		self.clearButton.clicked.connect(self.clear)

	def getResponse(self):
		return self.properties_form.getResponse()

	def clear(self):
		self.properties_form.clear()

	def testFill(self):
		self.properties_form.testFill()

class PreparationTab(QtGui.QWidget):
	"""
	Preparation tab widget. Users input the recipe preparation steps.
	"""
	oscm_signal = QtCore.pyqtSignal()
	def __init__(self,parent=None):
		super(PreparationTab,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.layout.setAlignment(QtCore.Qt.AlignRight)

		self.stackedFormWidget = QtGui.QStackedWidget()
		self.stackedFormWidget.setFrameStyle(QtGui.QFrame.StyledPanel)
		self.steps_list = QtGui.QListWidget()
		self.steps_list.setMaximumWidth(150)
		self.steps_list.currentRowChanged.connect(self.stackedFormWidget.setCurrentIndex)

		self.oscm_button = QtGui.QPushButton('Submit to OSCM')
		self.addStepButton = QtGui.QPushButton('Add Step')
		self.removeStepButton = QtGui.QPushButton('Remove Step')
		self.addStepButton.clicked.connect(self.addStep)
		self.removeStepButton.clicked.connect(self.removeStep)
		self.nextButton = QtGui.QPushButton('Next >>>')
		self.clearButton = QtGui.QPushButton('Clear Fields')
		self.clearButton.clicked.connect(self.clear)
		self.oscm_button.clicked.connect(self.handle_send_to_oscm)

		self.miniLayout = QtGui.QGridLayout()
		self.miniLayout.addWidget(self.addStepButton,0,0)
		self.miniLayout.addWidget(self.steps_list,1,0)
		self.miniLayout.addWidget(self.removeStepButton,2,0)
		self.recipeParams = FieldsFormWidget(fields=recipe_fields,model=recipe)
		self.layout.addLayout(self.miniLayout,0,0,3,1)
		self.layout.addWidget(self.recipeParams,0,1,1,2)
		self.layout.addWidget(self.stackedFormWidget,1,1,1,2)
		self.layout.addWidget(self.clearButton,2,1,1,1)
		self.layout.addWidget(self.oscm_button,2,2,1,1)
		self.layout.addWidget(self.nextButton,3,0,1,3)

	def testFill(self):
		self.recipeParams.testFill()
		for step in range(3):
			self.addStep()
			self.stackedFormWidget.currentWidget().testFill()
			self.stackedFormWidget.currentWidget().input_widgets['name'].setCurrentIndex(step)

	def addStep(self):
		"""
		Add another step. Adds new entry to step list and creates new step input widget.
		"""
		w = FieldsFormWidget(fields=preparation_fields,model=preparation_step)
		idx = self.stackedFormWidget.addWidget(w)
		self.stackedFormWidget.setCurrentIndex(idx)
		self.steps_list.addItem(w.input_widgets['name'].currentText())
		item = self.steps_list.item(idx)
		w.input_widgets['name'].activated[str].connect(item.setText)
		w.input_widgets['name'].activated[str].connect(
			lambda x: w.input_widgets['carbon_source'].hide() if x!='Growing' else w.input_widgets['carbon_source'].show())
		w.input_widgets['name'].activated[str].connect(
			lambda x: w.input_widgets['carbon_source_flow_rate'].hide() if x!='Growing' else w.input_widgets['carbon_source_flow_rate'].show())
		w.input_widgets['name'].activated[str].connect(
			lambda x: w.units_input['carbon_source_flow_rate'].hide() if x!='Growing' else w.units_input['carbon_source_flow_rate'].show())
		w.input_widgets['name'].activated[str].emit(w.input_widgets['name'].currentText())

	def removeStep(self):
		"""
		Removes step as selected from step list widget.
		"""
		x=self.steps_list.currentRow()
		self.stackedFormWidget.removeWidget(self.stackedFormWidget.widget(x))
		self.steps_list.takeItem(x)

	def getResponse(self):
		"""
		Returns a response dictionary containing:
		
		reparation_step:		A list of dictionary responses, as defined in FieldsFormWidget.getResponse() for each step.
		recipe:					A dictionary containing response from recipe input widget.
		"""
		prep_response = []
		for i in range(self.stackedFormWidget.count()):
			prep_response.append(self.stackedFormWidget.widget(i).getResponse())
		recipe_response = self.recipeParams.getResponse()

		return {'preparation_step':prep_response,'recipe':recipe_response}

	def clear(self):
		while self.steps_list.count()>0:
			self.steps_list.setCurrentRow(0)
			self.removeStep()
		self.recipeParams.clear()

	def getRecipeDict(self,preparation_response):
		with dal.session_scope() as session: 
			c = recipe()
			for field,item in preparation_response["recipe"].items():
				value = item['value']
				unit = item['unit']
				if value != None:
					if sql_validator['str'](getattr(recipe,field)) or sql_validator['int'](getattr(recipe,field)):
						setattr(c,field,value)
					elif sql_validator['float'](getattr(recipe,field)):
						value = float(value)
						setattr(c,field,value*getattr(recipe,field).info['conversions'][unit])
					else:
						value = int(value)
						setattr(c,field,value)
			session.add(c)
			session.commit()

			for step_idx, step in enumerate(preparation_response['preparation_step']):
				p = preparation_step()
				p.recipe_id = c.id
				p.step = step_idx
				for field,item in step.items():
					value = item['value']
					unit = item['unit']
					if value != None:
						if sql_validator['str'](getattr(preparation_step,field)) or sql_validator['int'](getattr(preparation_step,field)):
							setattr(p,field,value)
						elif sql_validator['float'](getattr(preparation_step,field)):
							value = float(value)
							setattr(p,field,value*getattr(preparation_step,field).info['conversions'][unit])
						else:
							value = int(value)
							setattr(p,field,value)
				session.add(p)
				session.commit()

			return c.json_encodable()

	def handle_send_to_oscm(self):
		preparation_response = self.getResponse()

		validator_response = [
			ReviewTab.validate_preparation(preparation_response),
			ReviewTab.validate_temperature(preparation_response),
			ReviewTab.validate_pressure(preparation_response),
			ReviewTab.validate_duration(preparation_response),
			ReviewTab.validate_base_pressure(preparation_response),
			ReviewTab.validate_carbon_source(preparation_response)
			]
			
		if any([v!=True for v in validator_response]):
			error_dialog = QtGui.QMessageBox(self)
			error_dialog.setWindowModality(QtCore.Qt.WindowModal)
			error_dialog.setText("Input Error!")
			error_dialog.setInformativeText("\n\n".join([v for v in validator_response if v != True]))
			error_dialog.exec()
			return

		# build oscm path
		oscm_dir = 'oscm_files'
		oscm_path = os.path.abspath(oscm_dir)

		# define filename
		filename = 'recipe.json'

		# preparation data. Here I just have JSON data for the example
		recipe_dict = self.getRecipeDict(preparation_response)

		# create file
		dump_file = open(os.path.join(oscm_path, filename), 'w')
		json.dump(recipe_dict,dump_file)
		dump_file.close()

		# Stop preparing recipe and go to oscm widget (not sure if this work!!!)
		self.oscm_signal.emit()
		
class FileUploadTab(QtGui.QWidget):
	"""
	File upload widget tab. Users upload SEM and Raman files as well as associated input.

	mode:	Upload method (local or nanohub)
	"""
	def __init__(self,parent=None,mode='local'):
		super(FileUploadTab,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.mode = mode
		self.sem_file_path = ''

		self.raman_list = QtGui.QListWidget()
		self.sem_list = QtGui.QListWidget()
		self.stackedRamanFormWidget = QtGui.QStackedWidget()
		self.stackedRamanFormWidget.setFrameStyle(QtGui.QFrame.StyledPanel)

		self.upload_sem = QtGui.QPushButton('Upload SEM Image')
		self.upload_raman = QtGui.QPushButton('Upload Raman Spectroscopy')
		self.remove_sem = QtGui.QPushButton('Remove SEM Image')
		self.remove_raman = QtGui.QPushButton('Remove Raman Spectroscopy')
		self.clearButton = QtGui.QPushButton('Clear Fields')
		self.wavelength_input = FieldsFormWidget(fields=['wavelength'],model=raman_file)

		self.nextButton = QtGui.QPushButton('Next >>>')
		spacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding)

		self.layout.addWidget(self.upload_sem,0,0,1,1)
		self.layout.addWidget(self.remove_sem,1,0,1,1)
		self.layout.addWidget(self.sem_list,0,1,3,1)
		self.layout.addWidget(self.upload_raman,3,0,1,1)
		self.layout.addWidget(self.wavelength_input,4,0,1,1)
		self.layout.addWidget(QtGui.QLabel("Characteristic Percentage (%):"),5,0,1,1)
		self.layout.addWidget(self.stackedRamanFormWidget,6,0,1,1)
		self.layout.addWidget(self.remove_raman,7,0,1,1)
		self.layout.addWidget(self.raman_list,3,1,5,1)
		self.layout.addItem(spacer,9,0,1,2)
		self.layout.addWidget(self.clearButton,8,0,1,2)
		self.layout.addWidget(self.nextButton,10,0,1,2)

		self.upload_sem.clicked.connect(self.importSEM)
		self.upload_raman.clicked.connect(self.importRaman)
		self.raman_list.currentRowChanged.connect(self.stackedRamanFormWidget.setCurrentIndex)
		self.remove_sem.clicked.connect(self.removeSEM)
		self.remove_raman.clicked.connect(self.removeRaman)
		self.clearButton.clicked.connect(self.clear)


	def removeSEM(self):
		x=self.sem_list.currentRow()
		self.sem_list.takeItem(x)

	def removeRaman(self):
		x=self.raman_list.currentRow()
		self.stackedRamanFormWidget.removeWidget(self.stackedRamanFormWidget.widget(x))
		self.raman_list.takeItem(x)

	def importSEM(self):
		self.sem_file_path = self.importFile()
		if isinstance(self.sem_file_path,str):
			self.sem_list.addItem(self.sem_file_path)

	def importRaman(self):
		self.raman_file_path = self.importFile()
		if isinstance(self.raman_file_path,str):
			if self.stackedRamanFormWidget.count() > 0:
				sm = sum([float(self.stackedRamanFormWidget.widget(i).text()) for i in range(self.stackedRamanFormWidget.count())])
			else:
				sm = 0
			self.raman_list.addItem(self.raman_file_path)
			w = QtGui.QLineEdit()
			w.setPlaceholderText("Input must be <= %s"%(100-sm))
			w.setValidator(QtGui.QDoubleValidator(0.,100.-sm,2))
			self.stackedRamanFormWidget.addWidget(w)
			self.stackedRamanFormWidget.setCurrentIndex(self.stackedRamanFormWidget.count()-1)

	def importFile(self):
		if self.mode == 'local':
			try:
				file_path = QtGui.QFileDialog.getOpenFileName()
				if isinstance(file_path,tuple):
					file_path = file_path[0]
				else:
					return
				return file_path
			except Exception as e:
				print(e)
				return
		elif self.mode == 'nanohub':
			try:
				file_path = subprocess.check_output('importfile',shell=True).strip().decode("utf-8")
				return file_path
			except Exception as e:
				print(e)
				return
		else:
				return

	def getResponse(self):
		"""
		Returns a response dictionary containing:
			SEM Image File:				The path to the SEM file.
			Raman Files:				A list of paths to the Raman files.
			Characteristic Percentage:	A list of percentages, where each entry represents the fraction of 
										the sample that each Raman file represents.
			Raman Wavelength:			The wavelength of the Raman spectroscopy.
		"""
		r = {
			'SEM Image Files': [self.sem_list.item(i).text() for i in range(self.sem_list.count())], 
			'Raman Files': [self.raman_list.item(i).text() for i in range(self.raman_list.count())],
			'Characteristic Percentage': [self.stackedRamanFormWidget.widget(i).text() for i in range(self.stackedRamanFormWidget.count())],
			'Raman Wavength': self.wavelength_input.getResponse()['wavelength']['value']}
		return r

	def clear(self):
		while self.raman_list.count()>0:
			self.raman_list.setCurrentRow(0)
			self.removeRaman()
		while self.sem_list.count()>0:
			self.sem_list.setCurrentRow(0)
			self.removeSEM()
		self.wavelength_input.clear()

class ReviewTab(QtGui.QScrollArea):
	"""
	Review tab widget. Allows users to look over input and submit. Validates data and then uploads to MDF.

	box_config_path:	Path to box configuration file
	"""
	def __init__(self,parent=None, box_config_path=None):
		super(ReviewTab,self).__init__(parent=parent)
		self.properties_response = None
		self.preparation_response = None
		self.files_response = None
		self.box_config_path = box_config_path
		self.submitButton = QtGui.QPushButton('Submit')

	def zipdir(self, path, ziph):
		"""
		Create a zipfile from a nested directory. Make the paths in the zip file
		relative to the root directory
		:param path: Path to the root directory
		:param ziph: zipfile handler
		:return:
		"""
		for root, dirs, files in os.walk(path):
			for file in files:
				ziph.write(os.path.join(root, file),
						   arcname=os.path.join(os.path.relpath(root, path),
												file))


	def upload_to_mdf(self,response_dict):
		import zipfile, time, shutil
		mdf_dir = 'mdf_%s'%time.time()
		os.mkdir(mdf_dir)
		mdf_path = os.path.abspath(mdf_dir)
		for f in response_dict['Raman Files']:
			if os.path.isfile(f):
				shutil.move(f,mdf_path)
		for f in response_dict['SEM Image Files']:
			if os.path.isfile(f):
				shutil.move(f,mdf_path)

		dump_file = open(os.path.join(mdf_path,'recipe.json'), 'w')
		json.dump(response_dict['json'],dump_file)
		dump_file.close()

		box_adaptor = BoxAdaptor(self.box_config_path)
		upload_folder = box_adaptor.create_upload_folder()

		zip_path = mdf_path + ".zip"
		zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
		self.zipdir(mdf_path, zipf)
		zipf.close()
		print("Uploading ", zip_path, " to box")

		box_file = box_adaptor.upload_file(upload_folder, zip_path, mdf_dir+'.zip')

		mdf = MDFAdaptor()
		return mdf.upload_recipe(Recipe(response_dict['json']), box_file)


	def refresh(self,properties_response,preparation_response,files_response,provenance_response):
		"""
		Refreshes the review fields.

		properties_response:		Response from PropertiesTab.getResponse().
		preparation_response:		Response from PreparationTab.getResponse().
		files_response:				Response from FileUploadTab.getResponse().
		provenance_response:		Response from ProvenanceTab.getResponse().
		"""
		self.properties_response = properties_response
		self.preparation_response = preparation_response
		self.files_response = files_response

		self.contentWidget = QtGui.QWidget()
		self.layout = QtGui.QGridLayout(self.contentWidget)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		
		propertiesLabel = QtGui.QLabel('Properties')
		propertiesLabel.setFont(label_font)
		preparationLabel = QtGui.QLabel('Recipe')
		preparationLabel.setFont(label_font)
		filesLabel = QtGui.QLabel('Files')
		filesLabel.setFont(label_font)
		authorsLabel = QtGui.QLabel('Authors')
		authorsLabel.setFont(label_font)

		# Author response
		self.layout.addWidget(authorsLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		for a,auth in enumerate(provenance_response['author']):
			row = self.layout.rowCount()
			self.layout.addWidget(QtGui.QLabel("%s, %s   [%s]"%(auth["last_name"]["value"],auth["first_name"]["value"],auth["institution"]["value"])))

		# Properties response
		self.layout.addWidget(propertiesLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		label = QtGui.QLabel()
		for field in properties_response.keys():
			info = getattr(properties,field).info
			row = self.layout.rowCount()
			value = properties_response[field]['value']
			unit = properties_response[field]['unit']
			label = QtGui.QLabel(info['verbose_name'])
			self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
			self.layout.addWidget(QtGui.QLabel(str(value)),row,1,QtCore.Qt.AlignRight|QtCore.Qt.AlignCenter)
			self.layout.addWidget(QtGui.QLabel(str(unit)),row,2,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
			self.layout.addItem(
				QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), hPolicy = QtGui.QSizePolicy.Expanding),
				row,
				3)

		# Preparation response
		self.layout.addItem(
			QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), vPolicy = QtGui.QSizePolicy.Fixed),
			self.layout.rowCount(),
			0)
		self.layout.addWidget(preparationLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		recipe_response = preparation_response['recipe']
		for field in recipe_response.keys():
			info = getattr(recipe,field).info
			row = self.layout.rowCount()
			value = recipe_response[field]['value']
			unit = recipe_response[field]['unit']
			label = QtGui.QLabel(info['verbose_name'])
			self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
			self.layout.addWidget(QtGui.QLabel(str(value)),row,1,QtCore.Qt.AlignRight|QtCore.Qt.AlignCenter)
			self.layout.addWidget(QtGui.QLabel(str(unit)),row,2,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
			self.layout.addItem(
				QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), hPolicy = QtGui.QSizePolicy.Expanding),
				row,
				3)	

		self.layout.addWidget(QtGui.QLabel("Preparation Steps:"),self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		for step, step_response in enumerate(preparation_response['preparation_step']):
			stepLabel = QtGui.QLabel('Step %s'%step)
			stepLabel.setFont(sublabel_font)
			self.layout.addWidget(stepLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
			for field in step_response.keys():
				info = getattr(preparation_step,field).info
				row = self.layout.rowCount()
				value = step_response[field]['value']
				unit = step_response[field]['unit']
				label = QtGui.QLabel(info['verbose_name'])
				self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
				self.layout.addWidget(QtGui.QLabel(str(value)),row,1,QtCore.Qt.AlignRight|QtCore.Qt.AlignCenter)
				self.layout.addWidget(QtGui.QLabel(str(unit)),row,2,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
				self.layout.addItem(
					QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), hPolicy = QtGui.QSizePolicy.Expanding),
					row,
					3)
		
		# File upload response
		self.layout.addItem(
			QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), vPolicy = QtGui.QSizePolicy.Fixed),
			self.layout.rowCount(),
			0)
		self.layout.addWidget(filesLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		self.layout.addWidget(QtGui.QLabel("SEM Image Files:"),self.layout.rowCount(),0)
		for k in range(len(files_response["SEM Image Files"])):
			row = self.layout.rowCount()
			name = files_response["SEM Image Files"][k]
			label = QtGui.QLabel("%s"%(name))
			self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
		
		self.layout.addWidget(QtGui.QLabel("Raman Wavength"),self.layout.rowCount(),0)
		self.layout.addWidget(QtGui.QLabel(files_response['Raman Wavength']),self.layout.rowCount(),1)
		self.layout.addWidget(QtGui.QLabel("Raman Spectroscopy Files:"),self.layout.rowCount(),0)
		for k in range(len(files_response["Raman Files"])):
			row = self.layout.rowCount()
			name = files_response["Raman Files"][k]
			pct = files_response["Characteristic Percentage"][k]
			label = QtGui.QLabel("[%s]  %s"%(pct,name))
			self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)

		self.layout.addWidget(self.submitButton,self.layout.rowCount(),0)

		self.setWidget(self.contentWidget)
		self.setWidgetResizable(True)

	@staticmethod
	def validate_temperature(preparation_response):
		for s,step in enumerate(preparation_response['preparation_step']):
			if step['furnace_temperature']['value'] == None:
				return "Missing input for field '%s' for Preparation Step %s (%s)."\
					%(preparation_step.furnace_temperature.info['verbose_name'],s,step['name']['value'])
		return True

	@staticmethod
	def validate_pressure(preparation_response):
		for s,step in enumerate(preparation_response['preparation_step']):
			if step['furnace_pressure']['value'] == None:
				return "Missing input for field '%s' for Preparation Step %s (%s)."\
					%(preparation_step.furnace_pressure.info['verbose_name'],s,step['name']['value'])
		return True

	@staticmethod
	def validate_base_pressure(preparation_response):
		if preparation_response['recipe']['base_pressure']['value'] == None:
			return "Missing input for field '%s' in Preparation."%(recipe.base_pressure.info['verbose_name'])
		else:
			return True

	@staticmethod
	def validate_duration(preparation_response):
		for s,step in enumerate(preparation_response['preparation_step']):
			if step['duration']['value'] == None:
				return "Missing input for field '%s' for preparation Step %s (%s)."\
					%(preparation_step.duration.info['verbose_name'],s,step['name']['value'])
		return True

	@staticmethod
	def validate_carbon_source(preparation_response):
		list_of_sources = [step["carbon_source"]["value"] for step
					  in preparation_response['preparation_step']
					  if step["carbon_source"]["value"] and step["name"]["value"]=='Growing']
		list_of_flows = [step["carbon_source_flow_rate"]["value"] for step
					  in preparation_response['preparation_step']
					  if step["carbon_source_flow_rate"]["value"] and step["name"]["value"]=='Growing']
		if len(list_of_sources) == 0:
			return "You must have at least one carbon source."
		if len(list_of_flows) != len(list_of_sources):
			return "You must have a flow rate for each carbon source."
		return True

	@staticmethod
	def validate_percentages(files_response):
		if len(files_response['Raman Files'])>0:
			try:
				sm = []
				for i in files_response['Characteristic Percentage']:
					if i != '':
						sm.append(float(i))
				sm = sum(sm)
			except:
				return "Please make sure you have input a characteristic percentage for all Raman spectra."
			if sm != 100:
				return "Characteristic percentages must sum to 100%. They currently sum to %s."%sm
			return True
		else:
			return True

	@staticmethod
	def validate_authors(provenance_response):
		if len(provenance_response['author'])==0:
			return "You must have at least one author."
		for a,auth in enumerate(provenance_response['author']):
			if len(auth['last_name']['value'])==0 or len(auth['first_name']['value'])==0:
				return "Author %s (input: %s, %s) must have a valid first and last name"%(a,auth['last_name']['value'],auth['first_name']['value'])
			if len(auth['institution'])==0:
				return "Author [%s, %s] must have a valid institution"%(auth['last_name']['value'],auth['first_name']['value'])
		return True

	@staticmethod
	def validate_preparation(preparation_response):
		if len(preparation_response['preparation_step'])==0:
			return "Missing preparation steps."
		else:
			return True

	def getFullResponse(self,properties_response,preparation_response,files_response, provenance_response):
		"""
		Checks and validates responses. If invalid, displays message box with problems. 
		Otherwise, it submits the full, validated response and returns the output response dictionary.

		properties_response:		Response from PropertiesTab.getResponse().
		preparation_response:		Response from PreparationTab.getResponse().
		files_response:				Response from FileUploadTab.getResponse().
		provenance_response:		Response from ProvenanceTab.getResponse().

		Validations performed:
			Ensures temperature input for each preparation step.
			Ensures pressure input for each preparation step.
			Ensures timestep input for each preparation step.
			Ensures base pressure input in properties.
			Ensures total characteristic percentages add up to 100.
			Ensures at least one author.

		Returns dictionary containing:
		json:			json encodable dictionary of 'sample' model.
		**kwargs:		All entries from files_response

		"""

		validator_response = [
			ReviewTab.validate_preparation(preparation_response),
			ReviewTab.validate_temperature(preparation_response),
			ReviewTab.validate_pressure(preparation_response),
			ReviewTab.validate_duration(preparation_response),
			ReviewTab.validate_base_pressure(preparation_response),
			ReviewTab.validate_percentages(files_response),
			ReviewTab.validate_authors(provenance_response),
			ReviewTab.validate_carbon_source(preparation_response)
			]
			
		if any([v!=True for v in validator_response]):
			error_dialog = QtGui.QMessageBox(self)
			error_dialog.setWindowModality(QtCore.Qt.WindowModal)
			error_dialog.setText("Input Error!")
			error_dialog.setInformativeText("\n\n".join([v for v in validator_response if v != True]))
			error_dialog.exec()
			return

		with dal.session_scope() as session:
			### SAMPLE DATASET ###
			s = sample()
			for field,item in provenance_response['sample'].items():
				value = item['value']
				if value != None:
					if sql_validator['str'](getattr(sample,field)) or sql_validator['int'](getattr(sample,field)):
						setattr(s,field,value)
					elif sql_validator['date'](getattr(sample,field)):
						setattr(s,field,value)
			session.add(s)
			session.commit()

			for f in files_response['SEM Image Files']:
				sf = sem_file()
				sf.sample_id = s.id
				sf.filename = os.path.basename(f)
				session.add(sf)
				session.commit()
			
			### RAMAN IS A SEPARATE DATASET FROM SAMPLE ###
			rs = raman_set()
			session.add(rs)
			session.commit()
			for ri,ram in enumerate(files_response['Raman Files']):
				rf = raman_file()
				rf.filename = os.path.basename(ram)
				rf.sample_id = s.id
				if files_response['Raman Wavength'] != None:
					rf.wavelength = files_response['Raman Wavength']
				session.add(rf)
				session.commit()

				params = GSARaman.auto_fitting(ram)
				r = raman_spectrum()
				r.raman_file_id = rf.id
				r.set_id = rs.id
				if files_response['Characteristic Percentage'] != None:
					r.percent = float(files_response['Characteristic Percentage'][ri]) 
				else:
					r.percent = 0.
				for peak in params.keys():
					for v in params[peak].keys():
						key = "%s_%s"%(peak,v)
						setattr(r,key,params[peak][v])
				session.add(r)
				session.commit()
			
			rs_fields = [
			"d_peak_shift",
			"d_peak_amplitude",
			"d_fwhm",
			"g_peak_shift",
			"g_peak_amplitude",
			"g_fwhm",
			"g_prime_peak_shift",
			"g_prime_peak_amplitude",
			"g_prime_fwhm"
			]
			for field in rs_fields:
				setattr(rs,field,sum([getattr(spect,field)*getattr(spect,'percent')/100. for spect in rs.raman_spectra]))
			rs.d_to_g = sum([getattr(spect,'d_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
			rs.gp_to_g = sum([getattr(spect,'g_prime_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
			session.commit()

			# Recipe
			c = recipe()
			c.sample_id = s.id
			for field,item in preparation_response["recipe"].items():
				value = item['value']
				unit = item['unit']
				if value != None:
					if sql_validator['str'](getattr(recipe,field)) or sql_validator['int'](getattr(recipe,field)):
						setattr(c,field,value)
					elif sql_validator['float'](getattr(recipe,field)):
						value = float(value)
						setattr(c,field,value*getattr(recipe,field).info['conversions'][unit])
					else:
						value = int(value)
						setattr(c,field,value)
			session.add(c)
			session.commit()

			# Properties
			pr = properties()
			pr.sample_id = s.id
			for field,item in properties_response.items():
				value = item['value']
				unit = item['unit']
				if value != None:
					if sql_validator['str'](getattr(properties,field)) or sql_validator['int'](getattr(properties,field)):
						setattr(pr,field,value)
					elif sql_validator['float'](getattr(properties,field)):
						value = float(value)
						setattr(pr,field,value*getattr(properties,field).info['conversions'][unit])
					else:
						value = int(value)
						setattr(pr,field,value)
			session.add(pr)
			session.commit()

			# Preparation Step
			for step_idx, step in enumerate(preparation_response['preparation_step']):
				p = preparation_step()
				p.recipe_id = c.id
				p.step = step_idx
				for field,item in step.items():
					value = item['value']
					unit = item['unit']
					if value != None:
						if sql_validator['str'](getattr(preparation_step,field)) or sql_validator['int'](getattr(preparation_step,field)):
							setattr(p,field,value)
						elif sql_validator['float'](getattr(preparation_step,field)):
							value = float(value)
							setattr(p,field,value*getattr(preparation_step,field).info['conversions'][unit])
						else:
							value = int(value)
							setattr(p,field,value)
				session.add(p)
				session.commit()

			for auth in provenance_response['author']:
				a = author()
				a.sample_id = s.id
				for field,item in auth.items():
					value = item['value']
					if value != None:
						setattr(a,field,value)
				session.add(a)
				session.commit()

			sample_json = s.json_encodable()
			raman_json = rs.json_encodable()
		full_response = {'json':sample_json}
		full_response.update(files_response)

		return full_response



	def submit(self,full_response):
		confirmation_dialog = QtGui.QMessageBox(self)
		confirmation_dialog.setText("Are you sure you want to submit this recipe?")
		confirmation_dialog.setInformativeText("Note: you will not be able to undo this submission.")
		confirmation_dialog.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
		confirmation_dialog.setWindowModality(QtCore.Qt.WindowModal)

		def upload_wrapper(btn):
			if btn.text() == "OK":
				try:
					dataset_id = self.upload_to_mdf(full_response)
					success_dialog = QtGui.QMessageBox(self)
					success_dialog.setText("Recipe successfully submitted.")
					success_dialog.setWindowModality(QtCore.Qt.WindowModal)
					success_dialog.exec()

				except MDFException as e:
					error_dialog = QtGui.QMessageBox(self)
					error_dialog.setWindowModality(QtCore.Qt.WindowModal)
					error_dialog.setText("Submission Error!")
					error_dialog.setInformativeText(str(e))
					error_dialog.exec()
					return

		confirmation_dialog.buttonClicked.connect(upload_wrapper)
		confirmation_dialog.exec()


def random_fill(field_name,model):
	import random, string, datetime
	field = getattr(model,field_name)
	if sql_validator['str'](field):
		return ''.join(random.choice(string.ascii_uppercase) for _ in range(10))
	elif sql_validator['int'](field):
		return np.random.randint(10)
	elif sql_validator['float'](field):
		return round(np.random.randn()*5+50,3)
	elif sql_validator['date'](field):
		return datetime.datetime.today()
	else:
		return None

def make_test_dict(test_sem_file=None,test_raman_file=None):
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)

	with dal.session_scope() as session:
		s = sample()
		for field in sample_fields:
			setattr(s,field,random_fill(field,sample))
		session.add(s)
		session.commit()

		if test_sem_file:
			sf = sem_file()
			sf.sample_id = s.id
			sf.filename = os.path.basename(test_sem_file)
			session.add(sf)
			session.commit()

		c = recipe()
		c.sample_id = s.id
		for field in recipe_fields:
			setattr(c,field,random_fill(field,recipe))
		session.add(c)
		session.commit()

		for n, name in enumerate(["Annealing","Growing","Cooling"]):
			p = preparation_step()
			p.recipe_id = c.id
			p.step = n
			p.name = name
			for field in preparation_fields:
				if field != "name":
					setattr(p,field,random_fill(field,preparation_step))
			session.add(p)
			session.commit()

		pr = properties()
		pr.sample_id = s.id
		for field in properties_fields:
			setattr(pr,field,random_fill(field,properties))
		session.add(pr)
		session.commit()

		for _ in range(3):
			a = author()
			a.sample_id = s.id
			for field in author_fields:
				setattr(a,field,random_fill(field,author))
			session.add(a)
			session.commit()

		if test_raman_file:
			rs = raman_set()
			session.add(rs)
			session.commit()
			for ri,ram in enumerate([test_raman_file]):
				rf = raman_file()
				rf.filename = os.path.basename(ram)
				rf.sample_id = s.id
				if files_response['Raman Wavength'] != None:
					rf.wavelength = 800
				session.add(rf)
				session.commit()

				params = GSARaman.auto_fitting(ram)
				r = raman_spectrum()
				r.raman_file_id = rf.id
				r.set_id = rs.id
				r.percent = 100.
				for peak in params.keys():
					for v in params[peak].keys():
						key = "%s_%s"%(peak,v)
						setattr(r,key,params[peak][v])
				session.add(r)
				session.commit()
			
			rs_fields = [
			"d_peak_shift",
			"d_peak_amplitude",
			"d_fwhm",
			"g_peak_shift",
			"g_peak_amplitude",
			"g_fwhm",
			"g_prime_peak_shift",
			"g_prime_peak_amplitude",
			"g_prime_fwhm"
			]
			for field in rs_fields:
				setattr(rs,field,sum([getattr(spect,field)*getattr(spect,'percent')/100. for spect in rs.raman_spectra]))
			rs.d_to_g = sum([getattr(spect,'d_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
			rs.gp_to_g = sum([getattr(spect,'g_prime_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
			session.commit()

		if test_raman_file:
			return s.json_encodable, rs.json_encodable()
		else:
			return s.json_encodable(), None


if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)

	app = QtGui.QApplication([])      
	submit = GSASubmit(box_config_path='box_config.json')
	if len(sys.argv) > 1 and sys.argv[1] == 'test':
		submit.test()
	submit.show()
	sys.exit(app.exec_())


