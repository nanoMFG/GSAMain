from __future__ import division
import numpy as np
import scipy as sc
import cv2, sys, time, json, copy, subprocess, os
from skimage import transform
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

from box_adaptor import BoxAdaptor
from gresq.database import sample, preparation_step, dal, Base, mdf_forge
from sqlalchemy import String, Integer, Float, Numeric
from gresq.config import config
from gresq.csv2db import build_db
from GSAQuery import GSAQuery
from GSAImage import GSAImage
from gresq.recipe import Recipe
from mdf_adaptor import MDFAdaptor
import pyqtgraph as pg

preparation_fields = [
	'name',
	'timestamp',
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

properties_fields = [
  "material_name",
  "catalyst",
  "tube_diameter",
  "cross_sectional_area",
  "tube_length",
  "base_pressure",
  "average_thickness_of_growth",
  "standard_deviation_of_growth",
  "number_of_layers",
  "growth_coverage",
  "domain_size",
  "shape",
  "thickness",
  "diameter",
  "length"
]

sql_validator = {
	'int': lambda x: isinstance(x.property.columns[0].type,Integer),
	'float': lambda x: isinstance(x.property.columns[0].type,Float),
	'str': lambda x: isinstance(x.property.columns[0].type,String)
}

label_font = QtGui.QFont("Helvetica", 28, QtGui.QFont.Bold)
sublabel_font = QtGui.QFont("Helvetica", 18)

class GSASubmit(QtGui.QTabWidget):
	def __init__(self,mode='local',parent=None):
		super(GSASubmit,self).__init__(parent=parent)
		self.mode = mode
		self.properties = PropertiesTab()
		self.preparation = PreparationTab()
		self.file_upload = FileUploadTab(mode=self.mode)
		self.review = ReviewTab()

		self.setTabPosition(QtGui.QTabWidget.South)
		self.addTab(self.preparation,'Preparation')
		self.addTab(self.properties,'Properties')
		self.addTab(self.file_upload,'File Upload')
		self.addTab(self.review, 'Review')

		self.currentChanged.connect(lambda x: self.review.refresh(
			properties_response = self.properties.getResponse(),
			preparation_response = self.preparation.getResponse(),
			files_response = self.file_upload.getResponse()) if x == self.indexOf(self.review) else None)

		self.review.submitButton.clicked.connect(lambda: self.review.fullResponse(
			properties_response = self.properties.getResponse(),
			preparation_response = self.preparation.getResponse(),
			files_response = self.file_upload.getResponse()
			))

		self.preparation.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.properties))
		self.properties.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.file_upload))
		self.file_upload.nextButton.clicked.connect(lambda: self.setCurrentWidget(self.review))

class PropertiesTab(QtGui.QWidget):
	def __init__(self,parent=None):
		super(PropertiesTab,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)

		self.properties_form = FieldsFormWidget(properties_fields,sample)
		self.nextButton = QtGui.QPushButton('Next >>>')

		self.layout.addWidget(self.properties_form,0,0)
		self.layout.addWidget(self.nextButton,1,0)

	def getResponse(self):
		return self.properties_form.getResponse()

class PreparationTab(QtGui.QWidget):
	def __init__(self,parent=None):
		super(PreparationTab,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.layout.setAlignment(QtCore.Qt.AlignRight)

		self.stackedFormWidget = QtGui.QStackedWidget()
		self.steps_list = QtGui.QListWidget()
		self.steps_list.setMaximumWidth(150)
		self.steps_list.currentRowChanged.connect(self.stackedFormWidget.setCurrentIndex)

		self.addStepButton = QtGui.QPushButton('Add Step')
		self.addStepButton.clicked.connect(self.addStep)
		self.nextButton = QtGui.QPushButton('Next >>>')

		self.miniLayout = QtGui.QGridLayout()
		self.miniLayout.addWidget(self.addStepButton,0,0)
		self.miniLayout.addWidget(self.steps_list,1,0)
		self.layout.addLayout(self.miniLayout,0,0)
		self.layout.addWidget(self.stackedFormWidget,0,1)
		self.layout.addWidget(self.nextButton,1,0,1,2)

	def addStep(self):
		w = FieldsFormWidget(fields=preparation_fields,model=preparation_step)
		idx = self.stackedFormWidget.addWidget(w)
		self.stackedFormWidget.setCurrentIndex(idx)
		self.steps_list.addItem(w.input_widgets['name'].currentText())
		item = self.steps_list.item(idx)
		w.input_widgets['name'].activated[str].connect(item.setText)

	def getResponse(self):
		response = []
		for i in range(self.stackedFormWidget.count()):
			response.append(self.stackedFormWidget.widget(i).getResponse())
		return response
			

class FieldsFormWidget(QtGui.QWidget):
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
				self.input_widgets[field] = QtGui.QComboBox()
				input_set = info['choices']
				with dal.session_scope() as session:
					if hasattr(mdf_forge,field):
						for v in session.query(getattr(mdf_forge,field)).distinct():
							if getattr(v,field) not in input_set:
								input_set.append(getattr(v,field))
				if 'choices' in info.keys():	
					self.input_widgets[field].addItems(input_set)
				self.input_widgets[field].addItem('Other')

				self.other_input[field] = QtGui.QLineEdit()
				self.other_input[field].setPlaceholderText('Enter other input here.')
				self.other_input[field].setFixedHeight(self.other_input[field].sizeHint().height())
				self.other_input[field].hide()
				
				self.input_widgets[field].activated[str].connect(
					lambda x, other_input = self.other_input[field]: other_input.show() if x == 'Other' else other_input.hide())
				self.layout.addWidget(self.input_widgets[field],row,3*col+1)	
				self.layout.addWidget(self.other_input[field],row,3*col+2)
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
		response = {}
		for field in self.fields:
			info = getattr(self.model,field).info
			response[field] = {}
			if isinstance(self.input_widgets[field],QtGui.QComboBox):
				if self.input_widgets[field] == 'Other':
					response[field]['value'] = self.other_input[field]
				else:
					response[field]['value'] = self.input_widgets[field].currentText()
				response[field]['unit'] = ''
			else:
				if sql_validator['int'](getattr(self.model,field)):
					response[field]['value'] = self.input_widgets[field].text() if self.input_widgets[field].text() != '' else None
				else:
					response[field]['value'] = self.input_widgets[field].text() if self.input_widgets[field].text() != '' else None
				if field in self.units_input.keys():
					response[field]['unit'] = self.units_input[field].currentText()
				else:
					response[field]['unit'] = ''

		return response
				
	
class FileUploadTab(QtGui.QWidget):
	def __init__(self,parent=None,mode='local'):
		super(FileUploadTab,self).__init__(parent=parent)
		self.layout = QtGui.QGridLayout(self)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.mode = mode
		self.sem_file_path = ''
		self.raman_file_path = ''

		self.upload_sem = QtGui.QPushButton('Upload SEM Image')
		self.upload_raman = QtGui.QPushButton('Upload Raman Spectroscopy')
	
		self.sem_label = QtGui.QLabel('No file uploaded.')
		self.raman_label = QtGui.QLabel('No file uploaded.')

		self.nextButton = QtGui.QPushButton('Next >>>')
		spacer = QtGui.QSpacerItem(
			self.nextButton.sizeHint().width(),
			self.nextButton.sizeHint().height(), 
			vPolicy = QtGui.QSizePolicy.Expanding)

		self.layout.addWidget(self.upload_sem,0,0)
		self.layout.addWidget(self.sem_label,0,1)
		self.layout.addWidget(self.upload_raman,1,0)
		self.layout.addWidget(self.raman_label,1,1)
		self.layout.addItem(spacer,2,0,1,2)
		self.layout.addWidget(self.nextButton,3,0,1,2)

		self.upload_sem.clicked.connect(self.importSEM)
		self.upload_raman.clicked.connect(self.importRaman)

	def importSEM(self):
		self.sem_file_path = self.importFile()
		if isinstance(self.sem_file_path,str):
			self.sem_label.setText(self.sem_file_path)

	def importRaman(self):
		self.raman_file_path = self.importFile()
		if isinstance(self.raman_file_path,str):
			self.raman_label.setText(self.raman_file_path)

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
		return {'SEM Image File': self.sem_file_path, 'Raman File': self.raman_file_path}

class ReviewTab(QtGui.QScrollArea):
	def __init__(self,parent=None):
		super(ReviewTab,self).__init__(parent=parent)
		self.properties_response = None
		self.preparation_response = None
		self.files_response = None
		self.submitButton = QtGui.QPushButton('Submit')
		self.submitButton.clicked.connect(lambda: self.upload_to_mdf())

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
		shutil.move(response_dict['Raman File'],mdf_path)
		shutil.move(response_dict['SEM Image File'],mdf_path)
		json.dumps(response_dict['json'],os.path.join(mdf_path,'recipe.json'))

		box_adaptor = BoxAdaptor("../box_config.json")
		upload_folder = box_adaptor.create_upload_folder()

		zip_path = mdf_path + ".zip"
		zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
		self.zipdir(mdf_path, zipf)
		zipf.close()
		print("Uploading ", zip_path, " to box")

		box_file = box_adaptor.upload_file(upload_folder, zip_path, mdf_dir+'.zip')
		mdf = MDFAdaptor()
		mdf.upload(Recipe(response_dict['json']), box_file)


	def refresh(self,properties_response,preparation_response,files_response):
		self.properties_response = properties_response
		self.preparation_response = preparation_response
		self.files_response = files_response

		self.contentWidget = QtGui.QWidget()
		self.layout = QtGui.QGridLayout(self.contentWidget)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		
		propertiesLabel = QtGui.QLabel('Properties')
		propertiesLabel.setFont(label_font)
		preparationLabel = QtGui.QLabel('Preparation Steps')
		preparationLabel.setFont(label_font)
		filesLabel = QtGui.QLabel('Files')
		filesLabel.setFont(label_font)

		self.layout.addWidget(propertiesLabel,0,0,QtCore.Qt.AlignLeft)
		label = QtGui.QLabel()
		for field in properties_response.keys():
			info = getattr(sample,field).info
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

		self.layout.addItem(
			QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), vPolicy = QtGui.QSizePolicy.Fixed),
			self.layout.rowCount(),
			0)
		self.layout.addWidget(preparationLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		for step, step_response in enumerate(preparation_response):
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
		
		self.layout.addItem(
			QtGui.QSpacerItem(label.sizeHint().width(),label.sizeHint().height(), vPolicy = QtGui.QSizePolicy.Fixed),
			self.layout.rowCount(),
			0)
		self.layout.addWidget(filesLabel,self.layout.rowCount(),0,QtCore.Qt.AlignLeft)
		for key in files_response.keys():
			row = self.layout.rowCount()
			value = QtGui.QLabel(str(files_response[key]))
			label = QtGui.QLabel(key)
			self.layout.addWidget(label,row,0,QtCore.Qt.AlignLeft|QtCore.Qt.AlignCenter)
			self.layout.addWidget(value,row,1,QtCore.Qt.AlignRight|QtCore.Qt.AlignCenter)

		self.layout.addWidget(self.submitButton,self.layout.rowCount(),0)

		self.setWidget(self.contentWidget)
		self.setWidgetResizable(True)

	def fullResponse(self,properties_response,preparation_response,files_response):
		with dal.session_scope() as session:
			s = sample()
			for field,item in properties_response.items():
				value = item['value']
				unit = item['unit']
				if value != None:
					if sql_validator['str'](getattr(sample,field)) or sql_validator['int'](getattr(sample,field)):
						setattr(s,field,value)
					elif sql_validator['float'](getattr(sample,field)):
						value = float(value)
						setattr(s,field,value*getattr(sample,field).info['conversions'][unit])
					else:
						value = int(value)
						setattr(s,field,value)
			session.add(s)
			session.commit()
			for step in preparation_response:
				p = preparation_step()
				p.sample_id = s.id
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


			json_file = s.json_encodable()
		full_response = {'json':json_file}
		full_response.update(files_response)
		return full_response



if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)

	app = QtGui.QApplication([])      
	submit = GSASubmit()
	submit.show()
	sys.exit(app.exec_())


