from __future__ import division
import numpy as np
import scipy as sc
import cv2, sys, time, json, copy, subprocess, os
from skimage import transform
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg

tic = time.time()

def slow_update(func, pause=0.3):
	def wrapper(self):
		global tic
		toc = time.time()
		if toc - tic > pause:
			tic = toc
			return func(self)
		else:
			pass
	return wrapper

class GSAImage:
	def __init__(self,mode='local'):
		self.mode = mode
		self.modifications = []
		self.selectedWidget = None

		if self.mode == 'nanohub':
			if 'TempGSA' not in os.listdir(os.getcwd()):
				os.mkdir('TempGSA')
			self.tempdir = os.path.join(os.getcwd(),'TempGSA')
			os.chdir(self.tempdir)

		self.mod_dict = {
		'Color Mask': ColorMask,
		'Canny Edge Detector': CannyEdgeDetection,
		'Dilate': Dilation,
		'Erode': Erosion,
		'Binary Mask': BinaryMask,
		'Find Contours': FindContours,
		'Filter Pattern': FilterPattern,
		'Blur': Blur,
		'Draw Scale': DrawScale,
		'Crop': Crop,
		'Domain Centers': DomainCenters,
		'Hough Transform': HoughTransform,
		'Erase': Erase,
		'Sobel Filter': SobelFilter
		}

		self.wComboBox = pg.ComboBox()
		for item in sorted(list(self.mod_dict)):
			self.wComboBox.addItem(item)

		self.wOpenFileBtn = QtGui.QPushButton('Import Image')
		self.wOpenFileBtn.clicked.connect(self.importImage)

		self.wAddMod = QtGui.QPushButton('Add')
		self.wAddMod.clicked.connect(lambda: self.addMod(mod=None))

		self.wRemoveMod = QtGui.QPushButton('Remove')
		self.wRemoveMod.clicked.connect(self.removeMod)

		self.wExportImage = QtGui.QPushButton('Export Image')
		self.wExportImage.clicked.connect(self.exportImage)

		self.wExportState = QtGui.QPushButton('Export State')
		self.wExportState.clicked.connect(self.exportState)

		self.wImportState = QtGui.QPushButton('Import State')
		self.wImportState.clicked.connect(self.importState)

		self.wModList = QtGui.QListWidget()
		self.wModList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.wModList.currentRowChanged.connect(self.selectMod)

		self.wMain = QtGui.QWidget()
		self.wMain.setFixedWidth(250)
		self.mainLayout = QtGui.QGridLayout()
		self.mainLayout.addWidget(self.wOpenFileBtn, 0,0)
		self.mainLayout.addWidget(self.wImportState, 0,1)
		self.mainLayout.addWidget(self.wModList,2,0,1,2)
		self.mainLayout.addWidget(self.wAddMod, 3,0)
		self.mainLayout.addWidget(self.wRemoveMod,3,1)
		self.mainLayout.addWidget(self.wComboBox,4,0,1,2)
		self.mainLayout.addWidget(self.wExportImage,5,0)
		self.mainLayout.addWidget(self.wExportState,5,1)
		self.wMain.setLayout(self.mainLayout)

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImgItem = pg.ImageItem()
		self.wImgBox_VB.addItem(self.wImgItem)
		self.wImgBox_VB.setAspectLocked(True)
		# self.wImgBox.setFixedWidth(400)

		self.wDetail = QtGui.QStackedWidget()
		# self.wDetail.setFixedWidth(400)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.wMain,0,0)
		self.layout.addWidget(self.wImgBox,0,1)
		self.layout.addWidget(self.wDetail,0,2)

		self.w = QtGui.QWidget()
		# self.w.setFixedHeight(600)
		self.w.setLayout(self.layout)

	@classmethod
	def viewOnlyWidget(cls,d):
		obj = cls()
		cla = globals()[d['@class']]
		obj.modifications = cla.from_dict(d,obj.wImgItem).tolist()
		obj.layout.removeWidget(obj.wMain)
		obj.wMain.hide()
		obj.layout.removeWidget(obj.wDetail)
		obj.wDetail.hide()
		obj.layout.addWidget(obj.wModList,0,0)
		obj.layout.setColumnStretch(0,1)
		obj.layout.setColumnStretch(1,3)
		obj.updateAll()
		return obj.w

	def exportImage(self):
		if len(self.modifications) > 0:
			if self.mode == 'local':
				name = QtWidgets.QFileDialog.getSaveFileName(None, "Export Image", '', "All Files (*);;PNG File (*.png);;JPEG File (*.jpg)")[0]
				if name != '':
					cv2.imwrite(name,self.modifications[-1].image())
			elif self.mode == 'nanohub':
				name = 'temp_%s.png'%int(time.time())
				cv2.imwrite(name,self.modifications[-1].image())
				subprocess.check_output('exportfile %s'%name,shell=True)
				# os.remove(name)
			else:
				return

	def exportState(self):
		if len(self.modifications) > 0:
			if self.mode == 'local':
				d = self.modifications[-1].to_dict()
				name = QtWidgets.QFileDialog.getSaveFileName(None, "Export Image", '', "All Files (*);;JSON File (*.json)")[0]
				if name != '':
					with open(name,'w') as f:
						json.dump(d,f)
			elif self.mode == 'nanohub':
				d = self.modifications[-1].to_dict()
				name = 'temp_%s.json'%int(time.time())
				with open(name,'w') as f:
					json.dump(d,f)
				subprocess.check_output('exportfile %s'%name,shell=True)
				# os.remove(name)
			else:
				return

	def importState(self):
		if self.mode == 'local':
			try:
				file_path = QtGui.QFileDialog.getOpenFileName()
				if isinstance(file_path,tuple):
					file_path = file_path[0]
				else:
					return
				self.clear()
				with open(file_path,'r') as f:
					state = json.load(f)
			except Exception as e:
				print(e)
				return
		elif self.mode == 'nanohub':
			try:
				file_path = subprocess.check_output('importfile',shell=True).strip().decode("utf-8")
				with open(file_path,'r') as f:
					state = json.load(f)
				os.remove(file_path)
			except Exception as e:
				print(e)
				return
		else:
			return

		cla = globals()[state['@class']]
		self.modifications = cla.from_dict(state,self.wImgItem).tolist()
		self.updateAll()

	def importImage(self):
		if self.mode == 'local':
			try:
				img_file_path = QtGui.QFileDialog.getOpenFileName()
				if isinstance(img_file_path,tuple):
					img_file_path = img_file_path[0]
				else:
					return
				self.clear()
				img_fname = img_file_path.split('/')[-1]
				img_data = cv2.imread(img_file_path)
				img_data = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)

				mod = InitialImage(img_item=self.wImgItem,properties={'mode':self.mode})
				mod.set_image(img_data)
				self.addMod(mod)
				self.w.setWindowTitle(img_fname)
			except Exception as e:
				print(e)
				return
		elif self.mode == 'nanohub':
			try:
				img_file_path = subprocess.check_output('importfile',shell=True).strip().decode("utf-8")
				img_fname = img_file_path.split('/')[-1]
				img_data = cv2.imread(img_file_path)
				img_data = cv2.cvtColor(img_data, cv2.COLOR_RGB2GRAY)

				os.remove(img_file_path)
				self.clear()

				mod = InitialImage(img_item=self.wImgItem,properties={'mode':self.mode})
				mod.set_image(img_data)
				self.addMod(mod)
				self.w.setWindowTitle(img_fname)
			except Exception as e:
				print(e)
				return
		else:
			return

	def updateAll(self):
		if len(self.modifications) == 0:
			self.clear()
		else:
			self.wModList.clear()
			while self.wDetail.count() > 0:
				self.wDetail.removeWidget(self.wDetail.widget(0))
			for i,mod in enumerate(self.modifications):
				self.wModList.addItem("%d %s"%(i,mod.name()))
				self.wDetail.addWidget(mod.widget())
			self.wModList.setCurrentRow(self.wModList.count()-1)

	def selectMod(self,index):
		if index >= 0:
			# try:
			self.modifications[index].update_view()
			# except:
				# pass
			self.wDetail.setCurrentIndex(index)
		elif self.wModList.count() > 0:
			self.wModList.setCurrentRow(self.wModList.count()-1)

	def clear(self):
		self.wImgItem.clear()
		self.wModList.clear()
		self.modifications = []
		while self.wDetail.count() > 0:
			self.wDetail.removeWidget(self.wDetail.widget(0))

	def removeMod(self):
		if len(self.modifications) > 1:
			self.wDetail.removeWidget(self.modifications[-1].widget())
			del[self.modifications[-1]]
			self.wModList.takeItem(self.wModList.count()-1)
			if self.wModList.count() > 0:
				self.wModList.setCurrentRow(self.wModList.count()-1)

	def addMod(self,mod=None):
		if mod == None:
			if len(self.modifications) > 0:
				mod = self.mod_dict[self.wComboBox.value()](self.modifications[-1],self.wImgItem,properties={'mode':self.mode})
			else:
				return
		self.modifications.append(mod)
		self.wDetail.addWidget(mod.widget())
		self.wModList.addItem("%d %s"%(self.wModList.count(),mod.name()))
		if self.wModList.count() > 0:
			self.wModList.setCurrentRow(self.wModList.count()-1)

	def widget(self):
		return self.w

	def run(self):
		self.w.show()

class Modification:
	def __init__(self,mod_in=None,img_item=None,properties={}):
		self.mod_in = mod_in
		self.img_item = img_item
		self.properties = properties
		if mod_in != None:
			self.img_out = self.mod_in.image()
		else:
			self.img_out = None

	def widget(self):
		return QtGui.QWidget()
	def image(self):
		return self.img_out.copy()
	def name(self):
		return 'Default Modification'
	def set_image(self,img):
		self.img_out = img.astype(np.uint8)
	def update_image(self):
		pass
	def update_view(self):
		self.update_image()
		self.img_item.setImage(self.img_out,levels=(0,255))
		return self.properties
	def delete_mod(self):
		return self.mod_in
	def tolist(self):
		if self.mod_in != None:
			return self.mod_in.tolist() + [self]
		else:
			return [self]
	def back_traverse(self,n):
		if n != 0:
			if self.mod_in == None:
				raise IndexError('Index out of range (n = %d)'%n)
			elif n != 0:
				return self.mod_in.back_traverse(n-1)
		elif n == 0:
			return self
	def root(self):
		if self.mod_in != None:
			return self.mod_in.root()
		else:
			return self
	def length(self):
		if self.mod_in != None:
			return self.mod_in.length()+1
		else:
			return 1
	def back_properties(self):
		if self.mod_in != None:
			d = self.mod_in.back_properties()
			d.update(self.properties)
			return d
		else:
			d = {}
			d.update(self.properties)
			return d
	def to_dict(self):
		d = {}
		d['@module'] = self.__class__.__module__
		d['@class'] = self.__class__.__name__
		d['date'] = time.asctime()
		if self.mod_in != None:
			d['mod_in'] = self.mod_in.to_dict()
		else:
			d['mod_in'] = None
		d['properties'] = self.properties
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		if d['mod_in'] != None:
			mod_in_dict = d['mod_in']
			mod_in_cls = globals()[mod_in_dict['@class']]
			mod_in = mod_in_cls.from_dict(mod_in_dict,img_item)
		else:
			mod_in = None
		return cls(mod_in,img_item,d['properties'])

class InitialImage(Modification):
	def name(self):
		return 'Initial Image'
	def to_dict(self):
		d = super(InitialImage,self).to_dict()
		d['img_out'] = self.img_out.tolist()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(InitialImage,cls).from_dict(d,img_item)
		obj.set_image(np.asarray(d['img_out']))
		return obj

class ColorMask(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(ColorMask,self).__init__(mod_in,img_item,properties)
		self.img_mask = None
		self.img_hist = self.img_item.getHistogram()

		self.wHistPlot = None
		self.lrItem = None

		self.wHistPlot = pg.PlotWidget()
		self.wHistPlot.plot(*self.img_hist)
		self.wHistPlot.setXRange(0,255)
		self.wHistPlot.hideAxis('left')

		self.lrItem = pg.LinearRegionItem((0,255),bounds=(0,255))
		self.lrItem.sigRegionChanged.connect(self.update_view)
		self.lrItem.sigRegionChangeFinished.connect(self.update_view)

		self.wHistPlot.addItem(self.lrItem)
		self.wHistPlot.setMouseEnabled(False,False)
		self.wHistPlot.setMaximumHeight(100)

	def to_dict(self):
		d = super(ColorMask,self).to_dict()
		d['img_mask'] = self.img_mask.tolist()
		d['LinearRegionItem'] = {'region':self.lrItem.getRegion()}
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(ColorMask,cls).from_dict(d,img_item)
		obj.img_mask = np.asarray(d['img_mask'])
		obj.lrItem.setRegion(d['LinearRegionItem']['region'])
		obj.update_image()
		obj.widget().hide()
		return obj

	def widget(self):
		return self.wHistPlot

	def update_image(self):
		minVal, maxVal = self.lrItem.getRegion()
		img = self.mod_in.image()
		self.img_mask = np.zeros_like(img)
		self.img_mask[np.logical_and(img>minVal,img<maxVal)] = 1
		self.img_out = img*self.img_mask+(1-self.img_mask)*255

	def name(self):
		return 'Color Mask'

class CannyEdgeDetection(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(CannyEdgeDetection,self).__init__(mod_in,img_item,properties)

		self.low_thresh = int(max(self.mod_in.image().flatten())*.1)
		self.high_thresh = int(max(self.mod_in.image().flatten())*.4)
		self.gauss_size = 5
		self.wToolBox = pg.LayoutWidget()
		self.wToolBox.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wGaussEdit = QtGui.QLineEdit(str(self.gauss_size))
		self.wGaussEdit.setValidator(QtGui.QIntValidator(3,51))
		self.wGaussEdit.setFixedWidth(60)

		self.wLowSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wLowSlider.setMinimum(0)
		self.wLowSlider.setMaximum(255)
		self.wLowSlider.setSliderPosition(int(self.low_thresh))
		self.wLowEdit = QtGui.QLineEdit(str(self.low_thresh))
		self.wLowEdit.setFixedWidth(60)
		self.wLowEdit.setValidator(QtGui.QIntValidator(0,255))

		self.wHighSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wHighSlider.setMinimum(0)
		self.wHighSlider.setMaximum(255)
		self.wHighSlider.setSliderPosition(int(self.high_thresh))
		self.wHighEdit = QtGui.QLineEdit(str(self.high_thresh))
		self.wHighEdit.setFixedWidth(60)
		self.wHighEdit.setValidator(QtGui.QIntValidator(0,255))

		self.wGaussEdit.returnPressed.connect(self._update_sliders)
		self.wLowSlider.sliderReleased.connect(self._update_texts)
		self.wLowSlider.sliderMoved.connect(self._update_texts)
		self.wLowEdit.returnPressed.connect(self._update_sliders)
		self.wHighSlider.sliderReleased.connect(self._update_texts)
		self.wHighSlider.sliderMoved.connect(self._update_texts)
		self.wHighEdit.returnPressed.connect(self._update_sliders)

		self.wToolBox.addWidget(QtGui.QLabel('Gaussian Size'),0,0)
		self.wToolBox.addWidget(QtGui.QLabel('Low Threshold'),1,0)
		self.wToolBox.addWidget(QtGui.QLabel('High Threshold'),3,0)
		self.wToolBox.addWidget(self.wGaussEdit,0,1)
		self.wToolBox.addWidget(self.wLowEdit,1,1)
		self.wToolBox.addWidget(self.wHighEdit,3,1)
		self.wToolBox.addWidget(self.wLowSlider,2,0,1,2)
		self.wToolBox.addWidget(self.wHighSlider,4,0,1,2)

	def to_dict(self):
		d = super(CannyEdgeDetection,self).to_dict()
		d['canny_inputs'] = {
			'low_threshold': self.low_thresh,
			'high_threshold': self.high_thresh,
			'gaussian_size': self.gauss_size
			}
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(CannyEdgeDetection,cls).from_dict(d,img_item)
		obj.low_thresh = d['canny_inputs']['low_threshold']
		obj.high_thresh = d['canny_inputs']['high_threshold']
		obj.gauss_size = d['canny_inputs']['gaussian_size']

		obj.wLowEdit.setText(str(obj.low_thresh))
		obj.wHighEdit.setText(str(obj.high_thresh))
		obj.wGaussEdit.setText(str(obj.gauss_size))

		obj.wGaussEdit.setText(str(obj.gauss_size))
		obj.wLowSlider.setSliderPosition(obj.low_thresh)
		obj.wHighSlider.setSliderPosition(obj.high_thresh)

		obj.update_image()
		obj.widget().hide()
		return obj

	def name(self):
		return 'Canny Edge Detection'

	def _update_sliders(self):
		self.gauss_size = int(self.wGaussEdit.text())
		self.gauss_size = self.gauss_size + 1 if self.gauss_size % 2 == 0 else self.gauss_size
		self.wGaussEdit.setText(str(self.gauss_size))
		self.low_thresh = int(self.wLowEdit.text())
		self.high_thresh = int(self.wHighEdit.text())

		self.wLowSlider.setSliderPosition(self.low_thresh)
		self.wHighSlider.setSliderPosition(self.high_thresh)

		self.update_view()

	def _update_texts(self):
		self.low_thresh = int(self.wLowSlider.value())
		self.high_thresh = int(self.wHighSlider.value())

		self.wLowEdit.setText(str(self.low_thresh))
		self.wHighEdit.setText(str(self.high_thresh))

		self.update_view()

	def update_image(self):
		self.img_out = cv2.GaussianBlur(self.mod_in.image(),(self.gauss_size,self.gauss_size),0)
		self.img_out = 255-cv2.Canny(self.img_out,self.low_thresh,self.high_thresh,L2gradient=True)

	def widget(self):
		return self.wToolBox

class Dilation(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(Dilation,self).__init__(mod_in,img_item,properties)
		self.size = 1
		self.wToolBox = pg.LayoutWidget()
		self.wToolBox.layout.setAlignment(QtCore.Qt.AlignTop)
		self.wSizeEdit = QtGui.QLineEdit(str(self.size))
		self.wSizeEdit.setValidator(QtGui.QIntValidator(1,20))
		self.wSizeEdit.setFixedWidth(60)
		self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSizeSlider.setMinimum(1)
		self.wSizeSlider.setMaximum(20)
		self.wSizeSlider.setSliderPosition(int(self.size))

		# self.wSizeSlider.sliderReleased.connect(self._update_texts)
		self.wSizeSlider.valueChanged.connect(self._update_texts)
		self.wSizeEdit.returnPressed.connect(self._update_sliders)

		self.wToolBox.addWidget(QtGui.QLabel('Kernel Size'),0,0)
		self.wToolBox.addWidget(self.wSizeEdit,0,1)
		self.wToolBox.addWidget(self.wSizeSlider,1,0,1,2)

	def to_dict(self):
		d = super(Dilation,self).to_dict()
		d['size'] = self.size
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(Dilation,cls).from_dict(d,img_item)
		obj.size = d['size']
		obj.wSizeSlider.setSliderPosition(d['size'])
		obj._update_texts()
		obj.widget().hide()
		return obj

	def name(self):
		return 'Dilation'

	def _update_sliders(self):
		self.size = int(self.wSizeEdit.text())
		self.wSizeSlider.setSliderPosition(self.size)
		self.update_view()

	def _update_texts(self):
		self.size = int(self.wSizeSlider.value())
		self.wSizeEdit.setText(str(self.size))
		self.update_view()

	def update_image(self):
		self.img_out = cv2.erode(self.mod_in.image(),np.ones((self.size,self.size),np.uint8),iterations=1)

	def widget(self):
		return self.wToolBox

class Erosion(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(Erosion,self).__init__(mod_in,img_item,properties)
		self.size = 1
		self.wToolBox = pg.LayoutWidget()
		self.wToolBox.layout.setAlignment(QtCore.Qt.AlignTop)
		self.wSizeEdit = QtGui.QLineEdit(str(self.size))
		self.wSizeEdit.setValidator(QtGui.QIntValidator(1,20))
		self.wSizeEdit.setFixedWidth(60)
		self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSizeSlider.setMinimum(1)
		self.wSizeSlider.setMaximum(20)
		self.wSizeSlider.setSliderPosition(int(self.size))

		# self.wSizeSlider.sliderReleased.connect(self._update_texts)
		self.wSizeSlider.valueChanged.connect(self._update_texts)
		self.wSizeEdit.returnPressed.connect(self._update_sliders)

		self.wToolBox.addWidget(QtGui.QLabel('Kernel Size'),0,0)
		self.wToolBox.addWidget(self.wSizeEdit,0,1)
		self.wToolBox.addWidget(self.wSizeSlider,1,0,1,2)

	def to_dict(self):
		d = super(Erosion,self).to_dict()
		d['size'] = self.size
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(Erosion,cls).from_dict(d,img_item)
		obj.size = d['size']
		obj.wSizeSlider.setSliderPosition(d['size'])
		obj._update_texts()
		obj.widget().hide()
		return obj

	def name(self):
		return 'Erosion'

	def _update_sliders(self):
		self.size = int(self.wSizeEdit.text())
		self.wSizeSlider.setSliderPosition(self.size)
		self.update_view()

	def _update_texts(self):
		self.size = int(self.wSizeSlider.value())
		self.wSizeEdit.setText(str(self.size))
		self.update_view()

	def update_image(self):
		self.img_out = cv2.dilate(self.mod_in.image(),np.ones((self.size,self.size),np.uint8),iterations=1)

	def widget(self):
		return self.wToolBox

class BinaryMask(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(BinaryMask,self).__init__(mod_in,img_item,properties)

	def to_dict(self):
		d = super(BinaryMask,self).to_dict()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(BinaryMask,cls).from_dict(d,img_item)
		obj.update_image()
		return obj

	def name(self):
		return 'Binary Mask'

	def update_image(self):
		self.img_out = self.mod_in.image()
		self.img_out[self.img_out < 255] = 0

class FindContours(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(FindContours,self).__init__(mod_in,img_item,properties)
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)
		self.img_inv = self.mod_in.image()
		self.img_inv[self.img_inv < 255] = 0
		self.img_inv = 255 - self.img_inv

		self.tol = 0.04
		self.wTolEdit = QtGui.QLineEdit(str(self.tol))
		self.wTolEdit.setValidator(QtGui.QDoubleValidator(0,1,3))
		self.wTolEdit.setFixedWidth(60)

		self.lowVert = 6
		self.wLowEdit = QtGui.QLineEdit(str(self.lowVert))
		self.wLowEdit.setValidator(QtGui.QIntValidator(3,100))
		self.wLowEdit.setFixedWidth(60)

		self.highVert = 6
		self.wHighEdit = QtGui.QLineEdit(str(self.highVert))
		self.wHighEdit.setValidator(QtGui.QIntValidator(3,100))
		self.wHighEdit.setFixedWidth(60)

		self.areaThresh = 0.5
		self.wThreshSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wThreshSlider.setMinimum(0)
		self.wThreshSlider.setMaximum(100)
		self.wThreshSlider.setSliderPosition(50)

		self._img, self.contours, self.hierarchy = cv2.findContours(
			self.img_inv,
			cv2.RETR_LIST,
			cv2.CHAIN_APPROX_SIMPLE)

		self.contour_dict = {}
		self.contour_area_max = 1

		self.wContourList = QtGui.QListWidget()
		self.wContourList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		for i,cnt in enumerate(self.contours):
			key = '%d Contour'%i
			self.contour_dict[key] = {}
			self.contour_dict[key]['index'] = i
			self.contour_dict[key]['list_item'] = QtGui.QListWidgetItem(key)
			self.contour_dict[key]['contour'] = cnt
			self.contour_dict[key]['area'] = cv2.contourArea(cnt,oriented=True)
			if abs(self.contour_dict[key]['area']) > self.contour_area_max:
				self.contour_area_max = abs(self.contour_dict[key]['area'])
		self.update_tol()

		self.wContourList.itemSelectionChanged.connect(self.update_view)
		self.wContourList.itemClicked.connect(self.update_view)
		self.wTolEdit.returnPressed.connect(self.update_tol)
		self.wLowEdit.returnPressed.connect(self.update_tol)
		self.wHighEdit.returnPressed.connect(self.update_tol)
		self.wThreshSlider.valueChanged.connect(self.update_tol)

		if len(self.contour_dict.keys())>0:
			self.wContourList.setCurrentItem(self.contour_dict['0 Contour']['list_item'])

		self.wLayout.addWidget(self.wContourList,0,0,2,1)
		self.wLayout.addWidget(QtGui.QLabel('Polygon Tolerance:'),3,0)
		self.wLayout.addWidget(self.wTolEdit,3,1)
		self.wLayout.addWidget(QtGui.QLabel('Vertex Tolerance:'),4,0)
		self.wLayout.addWidget(self.wLowEdit,4,1)
		self.wLayout.addWidget(self.wHighEdit,4,2)
		self.wLayout.addWidget(QtGui.QLabel('Contour Area Tolerance:'),5,0)
		self.wLayout.addWidget(self.wThreshSlider,6,0,1,3)

		self.update_view()

	def to_dict(self):
		d = super(FindContours,self).to_dict()
		d['line_tolerance'] = self.tol
		d['low_vertex_threshold'] = self.lowVert
		d['high_vertex_threshold'] = self.highVert
		d['contour_area_threshold'] = self.areaThresh
		d['threshold_slider_tick'] = self.wThreshSlider.value()
		d['contours'] = self.contours
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(FindContours,cls).from_dict(d,img_item)
		obj.tol = d['line_tolerance']
		obj.lowVert = d['low_vertex_threshold']
		obj.highVert = d['high_vertex_threshold']
		obj.areaThresh = d['contour_area_threshold']

		obj.wTolEdit.setText(str(obj.tol))
		obj.wLowEdit.setText(str(obj.lowVert))
		obj.wHighEdit.setText(str(obj.highVert))
		obj.wThreshSlider.setSliderPosition(d['threshold_slider_tick'])
		obj.update_image()

		obj.widget().hide()
		return obj

	def update_image(self):
		self.img_out = self.mod_in.image()
		selection = self.wContourList.selectedItems()
		if len(selection) == 1:
			cnt_key = selection[0].text()
			accept, approx = self.detect_poly(self.contour_dict[cnt_key]['contour'])
			cv2.drawContours(self.img_out,[approx],0,thickness=2,color=(0,255,0))

	def detect_poly(self,cnt):
		peri = cv2.arcLength(cnt, True)
		approx = cv2.approxPolyDP(cnt, self.tol * peri, True)
		return len(approx) >= self.lowVert and len(approx) <= self.highVert, approx

	def update_tol(self):
		self.tol = float(self.wTolEdit.text())
		self.lowVert = float(self.wLowEdit.text())
		self.highVert = float(self.wHighEdit.text())
		self.areaThresh = float(self.wThreshSlider.value())/100.
		self.wContourList.clear()
		for key in self.contour_dict.keys():
			cnt = self.contour_dict[key]['contour']
			area = self.contour_dict[key]['area']
			accept, approx = self.detect_poly(cnt)
			if accept and area < 0 and abs(area/self.contour_area_max) >= self.areaThresh:
				self.contour_dict[key]['list_item'] = QtGui.QListWidgetItem(key)
				self.wContourList.addItem(self.contour_dict[key]['list_item'])

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Find Contours'

class Blur(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(Blur,self).__init__(mod_in,img_item,properties)
		self.gauss_size = 5
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)
		self.wGaussEdit = QtGui.QLineEdit(str(self.gauss_size))
		self.wGaussEdit.setFixedWidth(100)
		self.wGaussEdit.setValidator(QtGui.QIntValidator(3,51))

		self.wLayout.addWidget(QtGui.QLabel('Gaussian Size:'),0,0)
		self.wLayout.addWidget(self.wGaussEdit,0,1)

		self.update_view()
		self.wGaussEdit.returnPressed.connect(self.update_view)

	def to_dict(self):
		d = super(Blur,self).to_dict()
		d['gaussian_size'] = self.gauss_size
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(Blur,cls).from_dict(d,img_item)
		obj.gauss_size = d['gaussian_size']
		obj.wGaussEdit.setText(str(obj.gauss_size))
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		self.gauss_size = int(self.wGaussEdit.text())
		self.gauss_size = self.gauss_size + 1 if self.gauss_size % 2 == 0 else self.gauss_size
		self.wGaussEdit.setText(str(self.gauss_size))
		self.img_out = cv2.GaussianBlur(self.mod_in.image(),(self.gauss_size,self.gauss_size),0)

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Blur'

class FilterPattern(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(FilterPattern,self).__init__(mod_in,img_item,properties)
		self.roi_size = 20
		self.scale = 1
		self.layer_list = []
		self.hover_mask = np.zeros_like(self.mod_in.image()).astype(np.uint8)
		self._item = None

		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wFilterList = QtGui.QListWidget()
		self.wFilterList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.wAdd = QtGui.QPushButton('Add Filter')
		self.wRemove = QtGui.QPushButton('Remove Layer')
		self.wErase = QtGui.QPushButton('Add Erase')
		self.wExportMask = QtGui.QPushButton('Export Mask')

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImgROI = ImageItemMask(self)
		self.wImgROI.setImage(self.img_item.image,levels=(0,255))
		self.wImgBox_VB.addItem(self.wImgROI)
		self.wImgBox_VB.setAspectLocked(True)

		self.wComboBox = pg.ComboBox()
		self.wComboBox.addItem('TM_SQDIFF')
		self.wComboBox.addItem('TM_SQDIFF_NORMED')
		self.wComboBox.addItem('TM_CCORR')
		self.wComboBox.addItem('TM_CCORR_NORMED')
		self.wComboBox.addItem('TM_CCOEFF')
		self.wComboBox.addItem('TM_CCOEFF_NORMED')

		self.method_dict = {
			'TM_SQDIFF': cv2.TM_SQDIFF,
			'TM_SQDIFF_NORMED': cv2.TM_SQDIFF_NORMED,
			'TM_CCORR': cv2.TM_CCORR,
			'TM_CCORR_NORMED': cv2.TM_CCORR_NORMED,
			'TM_CCOEFF': cv2.TM_CCOEFF,
			'TM_CCOEFF_NORMED': cv2.TM_CCOEFF_NORMED
		}

		self.wThreshSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wThreshSlider.setMinimum(1)
		self.wThreshSlider.setMaximum(1000)
		self.wThreshSlider.setSliderPosition(100)

		self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSizeSlider.setMinimum(2)
		self.wSizeSlider.setMaximum(50)
		self.wSizeSlider.setSliderPosition(5)

		self.wFilterAreaLabel = QtGui.QLabel('')
		self.wFilterScaleLabel = QtGui.QLabel('')

		self.wLayout.addWidget(QtGui.QLabel('Filter Method:'),0,0)
		self.wLayout.addWidget(self.wComboBox,0,1,1,3)
		self.wLayout.addWidget(QtGui.QLabel('Threshold:'),1,0)
		self.wLayout.addWidget(self.wThreshSlider,1,1,1,3)
		self.wLayout.addWidget(QtGui.QLabel('ROI Size:'),2,0)
		self.wLayout.addWidget(self.wSizeSlider,2,1,1,3)
		self.wLayout.addWidget(QtGui.QLabel('Area (um^2):'),3,0)
		self.wLayout.addWidget(self.wFilterAreaLabel,3,1)
		self.wLayout.addWidget(QtGui.QLabel('Scale (um/px):'),4,0)
		self.wLayout.addWidget(self.wFilterScaleLabel,4,1)
		self.wLayout.addWidget(self.wImgBox,9,0,4,4)
		self.wLayout.addWidget(self.wFilterList,5,0,4,3)
		self.wLayout.addWidget(self.wAdd,5,3)
		self.wLayout.addWidget(self.wRemove,8,3)
		self.wLayout.addWidget(self.wErase,6,3)
		self.wLayout.addWidget(self.wExportMask,7,3)

		self.wThreshSlider.valueChanged.connect(self.update_view)
		self.wComboBox.currentIndexChanged.connect(self.update_view)
		self.wSizeSlider.valueChanged.connect(self.update_view)
		self.wAdd.clicked.connect(self.addROI)
		self.wRemove.clicked.connect(self.removeLayer)
		self.wFilterList.itemSelectionChanged.connect(self.selectLayer)
		self.wErase.clicked.connect(self.addErase)
		self.wExportMask.clicked.connect(self.exportMask)

	def to_dict(self):
		d = super(FilterPattern,self).to_dict()
		d['layer_list'] = []
		for layer in self.layer_list:
			if layer['layer'] == 'filter':
				temp = {
					'roi':layer['roi'].saveState(),
					'threshold':layer['threshold'],
					'layer': 'filter',
					'mode': layer['mode']
					}
			else:
				temp = {
					'layer': 'erase',
				}
			temp['mask'] = layer['mask'].copy().tolist()
			d['layer_list'].append(temp)
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(FilterPattern,cls).from_dict(d,img_item)
		for layer in d['layer_list']:
			if layer['layer'] == 'filter':
				obj.addROI()
				temp = obj.layer_list[-1]
				temp['roi'].setState(layer['roi'])
				temp['threshold'] = layer['threshold']
				temp['mode'] = layer['mode']
				obj.wSizeSlider.setSliderPosition(layer['roi']['size'][0])
				obj.wThreshSlider.setSliderPosition(layer['threshold'])
				obj.wComboBox.setValue(layer['mode'])
			elif layer['layer'] == 'erase':
				obj.addErase()
				temp = obj.layer_list[-1]
			temp['mask'] = np.array(layer['mask'])

		obj.update_image()
		obj.widget().hide()

		return obj

	def addErase(self):
		erase_dict = {
				'layer': 'erase',
				'mask': np.zeros_like(self.mod_in.image(),dtype=bool)
			}
		self.layer_list.append(erase_dict)
		self.wFilterList.addItem('Erase %d'%self.wFilterList.count())
		self.wFilterList.setCurrentRow(self.wFilterList.count()-1)
		self.selectLayer()

	def erase(self,pos,radius=5):
		selection = self.wFilterList.selectedItems()
		if self._item['layer']=='erase' and len(selection) > 0:
			selection = selection[0]
			row = self.wFilterList.row(selection)
			if row == self.wFilterList.count() - 1:
				pos = [int(pos.x()), int(pos.y())]
				a, b = pos[0],pos[1]
				nx,ny = self._item['mask'].shape

				x,y = np.ogrid[-a:nx-a, -b:ny-b]
				mask = x*x + y*y <= radius**2
				self._item['mask'][mask] = True
				slow_update(self.update_view())

	def addROI(self):
		roi = pg.ROI(
			pos=(0,0),
			size=(self.roi_size,self.roi_size),
			removable=True,
			pen=pg.mkPen(color='r',width=2),
			maxBounds=self.wImgROI.boundingRect(),
			scaleSnap=True,
			snapSize=2)
		roi.sigRegionChanged.connect(self.update_view)
		self.wImgBox_VB.addItem(roi)
		roi_dict = {
			'roi':roi,
			'threshold':100,
			'mask': np.zeros_like(self.mod_in.image()),
			'layer': 'filter',
			'mode': None
			}
		self.layer_list.append(roi_dict)
		self.wFilterList.addItem('Filter %d'%self.wFilterList.count())
		self.wFilterList.setCurrentRow(self.wFilterList.count()-1)
		self.selectLayer()

	def removeLayer(self):
		if len(self.layer_list) > 0:
			if self.layer_list[-1]['layer'] == 'filter':
				self.wImgBox_VB.removeItem(self.layer_list[-1]['roi'])
			del self.layer_list[-1]
			self.wFilterList.takeItem(self.wFilterList.count()-1)
			if len(self.layer_list) > 0:
				self._item = self.layer_list[-1]
				self.wFilterList.setCurrentRow(self.wFilterList.count()-1)
				self.selectLayer()
			else:
				self._item = None

	def selectLayer(self):
		selection = self.wFilterList.selectedItems()
		if len(selection) == 1:
			selection = selection[0]
			row = self.wFilterList.row(selection)
			self._item = self.layer_list[row]
			self.wImgROI.setImage(self.mod_in.image(),levels=(0,255))
			if self._item['layer'] == 'filter':
				roi = self._item['roi']
				if self._item['mode'] != None:
					self.wComboBox.setValue(self._item['mode'])
				self.wSizeSlider.setSliderPosition(int(roi.size()[0]/2))
				self.wThreshSlider.setSliderPosition(self._item['threshold'])
			else:
				roi = None

			for r,ro in enumerate(self.layer_list):
				if ro['layer'] == 'filter':
					if r != row:
						ro['roi'].hide()
					else:
						ro['roi'].show()
		else:
			self._item = None

		self.update_view()

	def exportMask(self):
		if len(self.layer_list) > 0:
			if self.properties['mode'] == 'local':
				name = QtWidgets.QFileDialog.getSaveFileName(None, "Export Mask", '', "All Files (*);;Images (*.json)")[0]
				if name != '':
					with open(name,'w') as f:
						json.dump(self.mask_total.tolist(),f)
			elif self.properties['mode'] == 'nanohub':
				name = 'temp_%s.json'%int(time.time())
				with open(name,'w') as f:
					json.dump(self.mask_total.tolist(),f)
				subprocess.check_output('exportfile %s'%name,shell=True)
				# os.remove(name)
			else:
				return

	def update_image(self):
		back_properties = self.back_properties()
		self.eraser_size = int(self.wSizeSlider.value())
		if 'scale' in back_properties.keys():
			self.scale = back_properties['scale']
		try:
			self.img_out = self.mod_in.image()
			self.roi_img = self.mod_in.image()
			self.roi_img = cv2.cvtColor(self.roi_img,cv2.COLOR_GRAY2BGR)
			if self._item != None:
				if self._item['layer'] == 'filter':
					roi = self._item['roi']

					roi_size = 2*int(self.wSizeSlider.value())
					if roi_size != roi.size()[0]:
						roi.setSize([roi_size,roi_size])
					self._item['mode'] = self.wComboBox.value()
					self._item['threshold'] = self.wThreshSlider.value()

					region = roi.getArrayRegion(self.mod_in.image(),self.wImgROI).astype(np.uint8)
					x,y = region.shape
					padded_image = cv2.copyMakeBorder(self.mod_in.image(),int(y/2-1),int(y/2),int(x/2-1),int(x/2),cv2.BORDER_REFLECT_101)
					res = cv2.matchTemplate(padded_image,region,self.method_dict[self._item['mode']])

					if 'NORMED' in self._item['mode']:
						maxVal = 1
					else:
						maxVal = res.flatten().max()
					threshold = maxVal * np.logspace(-3,0,1000)[self._item['threshold']-1]
					self._item['mask'] = np.zeros_like(self.img_out).astype(bool)
					self._item['mask'][res < threshold] = True

				self.mask_total = np.zeros_like(self.img_out).astype(bool)
				selection = self.wFilterList.selectedItems()
				selection = selection[0]
				row = self.wFilterList.row(selection)
				for layer in self.layer_list[:row+1]:
					if layer['layer'] == 'filter':
						self.mask_total[layer['mask']] = True
					elif layer['layer'] == 'erase':
						self.mask_total[layer['mask']] = False

				self.roi_img = self.mod_in.image()
				self.roi_img = cv2.cvtColor(self.roi_img,cv2.COLOR_GRAY2BGR)
				self.img_out[np.logical_not(self.mask_total)] = 255
				self.roi_img[self.mask_total,:] = [0,0,255]
				if self._item['layer']=='erase':
					self.roi_img[self.hover_mask.astype(bool),:] = [0,255,0]

				self.properties['masked_area_um2'] = float(np.sum(self.mask_total)*self.scale**2)
				self.properties['mask_total'] = self.mask_total.tolist()
		except Exception as e:
			print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

	def update_view(self):
		self.update_image()
		if 'masked_area_um2' in self.properties.keys():
			self.wFilterAreaLabel.setNum(self.properties['masked_area_um2'])
		self.wFilterScaleLabel.setNum(self.scale)
		self.img_item.setImage(self.img_out,levels=(0,255))
		self.wImgROI.setImage(self.roi_img)

		return self.properties

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Filter Pattern'

class Crop(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(Crop,self).__init__(mod_in,img_item,properties)
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImgROI = pg.ImageItem()
		self.wImgROI.setImage(self.img_item.image,levels=(0,255))
		self.wImgBox_VB.addItem(self.wImgROI)
		self.wImgBox_VB.setAspectLocked(True)
		# self.wImgBox_VB.setMouseEnabled(False,False)

		self.roi = pg.ROI(
			pos=(0,0),
			size=(20,20),
			removable=True,
			pen=pg.mkPen(color='r',width=2),
			maxBounds=self.wImgROI.boundingRect(),)
		self.roi.addScaleHandle(pos=(1,1),center=(0,0))
		self.wImgBox_VB.addItem(self.roi)
		self.roi.sigRegionChanged.connect(self.update_view)

		self.wLayout.addWidget(self.wImgBox,0,0)

	def to_dict(self):
		d = super(Crop,self).to_dict()
		d['roi_state'] = self.roi.saveState()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(Crop,cls).from_dict(d,img_item)
		obj.roi.setState(d['roi_state'])
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		self.img_out = self.roi.getArrayRegion(self.wImgROI.image,self.wImgROI)
		self.img_out = self.img_out.astype(np.uint8)

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Crop'

class HoughTransform(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(HoughTransform,self).__init__(mod_in,img_item,properties)
		self.inv_img = 255 - self.mod_in.image()
		self.img_out = self.mod_in.image()
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)
		self.thresh_tick = 100
		self.min_angle = 10
		self.min_dist = 9
		self.line_length = 50
		self.line_gap = 10
		self.hspace,self.angles,self.distances = transform.hough_line(self.inv_img)
		self.bgr_img = cv2.cvtColor(self.img_out,cv2.COLOR_GRAY2BGR)
		self.bgr_hough = 255-np.round(self.hspace/np.max(self.hspace)*255).astype(np.uint8)
		self.bgr_hough = cv2.cvtColor(self.bgr_hough,cv2.COLOR_GRAY2BGR)


		self.properties['hough_transform'] = {
			'angles': self.angles,
			'distances': self.distances,
			'hspace': self.hspace
		}

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wHough = pg.ImageItem()
		# self.wHough.setImage(self.hspace,levels=(0,255))
		self.wImgBox_VB.addItem(self.wHough)
		# self.wImgBox_VB.setAspectLocked(True)
		# self.wImgBox_VB.setMouseEnabled(False,False)

		self.wHistPlot = pg.PlotWidget(title='Angle Histogram')
		self.wHistPlot.setXRange(0,180)
		self.wHistPlot.hideAxis('left')

		self.wMinAngleSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wMinAngleSlider.setMinimum(5)
		self.wMinAngleSlider.setMaximum(180)
		self.wMinAngleSlider.setSliderPosition(self.min_angle)

		self.wMinDistSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wMinDistSlider.setMinimum(5)
		self.wMinDistSlider.setMaximum(200)
		self.wMinDistSlider.setSliderPosition(self.min_dist)

		self.wThreshSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wThreshSlider.setMinimum(0)
		self.wThreshSlider.setMaximum(200)
		self.wThreshSlider.setSliderPosition(self.thresh_tick)

		self.wLengthSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wLengthSlider.setMinimum(10)
		self.wLengthSlider.setMaximum(200)
		self.wLengthSlider.setSliderPosition(self.line_length)

		self.wGapSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wGapSlider.setMinimum(5)
		self.wGapSlider.setMaximum(100)
		self.wGapSlider.setSliderPosition(self.line_gap)

		self.wLayout.addWidget(QtGui.QLabel('Minimum Angle:'),0,0)
		self.wLayout.addWidget(self.wMinAngleSlider,0,1)
		self.wLayout.addWidget(QtGui.QLabel('Minimum Distance:'),1,0)
		self.wLayout.addWidget(self.wMinDistSlider,1,1)
		self.wLayout.addWidget(QtGui.QLabel('Threshold:'),2,0)
		self.wLayout.addWidget(self.wThreshSlider,2,1)
		self.wLayout.addWidget(self.wImgBox,3,0,2,2)
		self.wLayout.addWidget(QtGui.QLabel('Minimum Line Length:'),5,0)
		self.wLayout.addWidget(self.wLengthSlider,5,1)
		self.wLayout.addWidget(QtGui.QLabel('Minimum Gap Length:'),6,0)
		self.wLayout.addWidget(self.wGapSlider,6,1)
		self.wLayout.addWidget(self.wHistPlot,7,0,2,2)

		self.wThreshSlider.valueChanged.connect(self.update_image)
		self.wMinAngleSlider.valueChanged.connect(self.update_image)
		self.wMinDistSlider.valueChanged.connect(self.update_image)
		self.wLengthSlider.valueChanged.connect(self.update_image)
		self.wGapSlider.valueChanged.connect(self.update_image)

		self.update_view()

	def to_dict(self):
		d = super(HoughTransform,self).to_dict()
		d['hough_line_peaks'] = {
			'min_distance': self.min_dist,
			'min_angle': self.min_angle,
			'threshold': self.threshold
		}
		d['probabilistic_hough_line'] = {
			'threshold': self.threshold,
			'line_length': self.line_length,
			'line_gap': self.line_gap
		}
		d['threshold_slider_tick'] = self.thresh_tick
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(HoughTransform,obj).from_dict(d,img_item)
		obj.wMinAngleSlider.setSliderPosition(str(d['hough_line_peaks']['min_angle']))
		obj.wMinDistSlider.setSliderPosition(str(d['hough_line_peaks']['min_distance']))
		obj.wThreshSlider.setSliderPosition(str(d['hough_line_peaks']['threshold']))
		obj.wLengthSlider.setSliderPosition(str(d['probabilistic_hough_line']['line_length']))
		obj.wGapSlider.setSliderPosition(str(d['probabilistic_hough_line']['line_gap']))
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		self.thresh_tick = int(self.wThreshSlider.value())
		self.threshold = int(np.max(self.hspace)*self.wThreshSlider.value()/200)
		self.min_angle = int(self.wMinAngleSlider.value())
		self.min_dist = int(self.wMinDistSlider.value())
		self.line_length = int(self.wLengthSlider.value())
		self.line_gap = int(self.wGapSlider.value())

		accum, angles, dists = transform.hough_line_peaks(
			self.hspace,
			self.angles,
			self.distances,
			min_distance = self.min_dist,
			min_angle = self.min_angle,
			threshold = self.threshold)

		# angle_diffs = []
		# for i,a1 in enumerate(angles):
		#   for j,a2 in enumerate(angles):
		#     if i < j:
		#       angle_diffs.append(abs(a1-a2)*180)

		y,x = np.histogram(np.array(angles)*180,bins=np.linspace(0,180,180))
		self.wHistPlot.clear()
		self.wHistPlot.plot(x,y,stepMode=True,fillLevel=0,brush=(0,0,255,150))

		lines = transform.probabilistic_hough_line(
			self.inv_img,
			threshold=self.threshold,
			line_length=self.line_length,
			line_gap=self.line_gap)

		self.bgr_hough = 255-np.round(self.hspace/np.max(self.hspace)*255).astype(np.uint8)
		self.bgr_hough = cv2.cvtColor(self.bgr_hough,cv2.COLOR_GRAY2BGR)

		for a,d in zip(angles,dists):
			angle_idx = np.nonzero(a == self.angles)[0]
			dist_idx = np.nonzero(d == self.distances)[0]
			cv2.circle(self.bgr_hough,center=(angle_idx,dist_idx),radius=5,color=(0,0,255),thickness=-1)

		self.bgr_img = self.mod_in.image()
		self.bgr_img = cv2.cvtColor(self.bgr_img,cv2.COLOR_GRAY2BGR)

		for p1,p2 in lines:
			cv2.line(self.bgr_img,p1,p2,color=(0,0,255),thickness=2)


		self.update_view()

	def update_view(self):
		self.wHough.setImage(self.bgr_hough)
		self.img_item.setImage(self.bgr_img)


		return self.properties

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Hough Transform'

class DomainCenters(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(DomainCenters,self).__init__(mod_in,img_item,properties)
		self.roi_list = []
		self.properties['centers'] = []
		self.properties['scale'] = 1
		self.img_out = self.mod_in.image()
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImg = ImageItemCenters(self,self.img_out)
		self.wImg.setImage(self.img_item.image,levels=(0,255))
		self.wImgBox_VB.addItem(self.wImg)
		self.wImgBox_VB.setAspectLocked(True)
		# self.wImgBox_VB.setMouseEnabled(False,False)
		self.wRemove = QtGui.QPushButton('Remove')
		self.wDDLabel = QtGui.QLabel('0')

		self.wLayout.addWidget(self.wImgBox,0,0,4,3)
		self.wLayout.addWidget(self.wRemove,5,0)
		self.wLayout.addWidget(QtGui.QLabel('Domain Density:'),5,1)
		self.wLayout.addWidget(self.wDDLabel,5,2)

		self.wRemove.clicked.connect(self.wImg.removeCenter)

	def to_dict(self):
		d = super(DomainCenters,self).to_dict()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(DomainCenters,obj).from_dict(d,img_item)
		for pos in obj.properties['centers']:
			obj.wImg.drawCircle(pos)
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		back_properties = self.back_properties()
		if 'scale' in back_properties.keys():
			self.properties['scale'] = back_properties['scale']
		x,y = self.img_out.shape
		self.properties['total_area'] = x*y*self.properties['scale']**2
		self.properties['domain_density'] = float(len(self.properties['centers']))/self.properties['total_area']
		self.wDDLabel.setNum(self.properties['domain_density'])

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Domain Centers'

class DrawScale(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(DrawScale,self).__init__(mod_in,img_item,properties)
		self.properties['scale'] = 1

		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImgROI = pg.ImageItem()
		self.wImgROI.setImage(self.img_item.image,levels=(0,255))
		self.wImgBox_VB.addItem(self.wImgROI)
		self.wImgBox_VB.setAspectLocked(True)
		# self.wImgBox_VB.setMouseEnabled(False,False)

		self.wPixels = QtGui.QLabel('1')
		self.wPixels.setFixedWidth(60)
		self.wScale = QtGui.QLabel('1')
		self.wScale.setFixedWidth(60)

		self.wLengthEdit = QtGui.QLineEdit(str(self.properties['scale']))
		self.wLengthEdit.setFixedWidth(60)
		self.wLengthEdit.setValidator(QtGui.QDoubleValidator())
		x,y = self.mod_in.image().shape
		self.roi = pg.LineSegmentROI([[int(x/2),int(y/4)],[int(x/2),int(3*y/4)]])
		self.wImgBox_VB.addItem(self.roi)

		self.wLayout.addWidget(QtGui.QLabel('# Pixels:'),0,0)
		self.wLayout.addWidget(self.wPixels,0,1)

		self.wLayout.addWidget(QtGui.QLabel('Length (um):'),1,0)
		self.wLayout.addWidget(self.wLengthEdit,1,1)

		self.wLayout.addWidget(QtGui.QLabel('Scale (um/px):'),2,0)
		self.wLayout.addWidget(self.wScale,2,1)

		self.wLayout.addWidget(self.wImgBox,3,0,4,4)

		self.roi.sigRegionChanged.connect(self.update_view)
		self.wLengthEdit.returnPressed.connect(self.update_view)

	def to_dict(self):
		d = super(DrawScale,self).to_dict()
		d['roi_state'] = self.roi.saveState()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(DrawScale,cls).from_dict(d,img_item)
		obj.roi.setState(d['roi_state'])
		obj.wLengthEdit.setText(str(d['properties']['scale_length_um']))
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		self.properties['num_pixels'] = len(self.roi.getArrayRegion(self.mod_in.image(),self.img_item))
		self.wPixels.setNum(self.properties['num_pixels'])
		self.properties['scale_length_um'] = float(self.wLengthEdit.text())
		if self.properties['num_pixels'] != 0:
			self.properties['scale'] = self.properties['scale_length_um'] / self.properties['num_pixels']
		self.wScale.setText(str(self.properties['scale']))

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Draw Scale'

class Erase(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(Erase,self).__init__(mod_in,img_item,properties)
		self.img_out = self.mod_in.image()
		self.eraser_size = 10
		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wImgBox = pg.GraphicsLayoutWidget()
		self.wImgBox_VB = self.wImgBox.addViewBox(row=1,col=1)
		self.wImgROI = pg.ImageItem()
		self.wImgROI.setImage(self.img_out,levels=(0,255))
		self.wImgBox_VB.addItem(self.wImgROI)
		self.wImgBox_VB.setAspectLocked(True)

		self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSizeSlider.setMinimum(1)
		self.wSizeSlider.setMaximum(100)
		self.wSizeSlider.setSliderPosition(self.eraser_size)

		kern = (np.ones((self.eraser_size,self.eraser_size))*255).astype(np.uint8)
		self.wImgROI.setDrawKernel(kern, mask=None, center=(int(self.eraser_size/2),int(self.eraser_size/2)), mode='set')
		self.wSizeSlider.valueChanged.connect(self.update_view)

		self.wLayout.addWidget(QtGui.QLabel('Eraser Size:'),0,0)
		self.wLayout.addWidget(self.wSizeSlider,0,1)
		self.wLayout.addWidget(self.wImgBox,1,0,4,4)

	def to_dict(self):
		d = super(Erase,self).to_dict()
		d['eraser_size'] = self.eraser_size
		d['erased_image'] = self.img_out.tolist()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(Erase,cls).from_dict(d,img_item)
		obj.eraser_size = d['eraser_size']
		obj.wSizeSlider.setSliderPosition(d['eraser_size'])
		obj.wImgROI.setImage(np.array(d['erased_image']),levels=(0,255))
		obj.update_image()

		obj.widget().hide()
		return obj

	def update_image(self):
		self.eraser_size = int(self.wSizeSlider.value())
		kern = (np.ones((self.eraser_size,self.eraser_size))*255).astype(np.uint8)
		self.wImgROI.setDrawKernel(kern, mask=None, center=(int(self.eraser_size/2),int(self.eraser_size/2)), mode='set')
		self.img_out = self.wImgROI.image

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Erase'

class SobelFilter(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(SobelFilter,self).__init__(mod_in,img_item,properties)
		self.sobel_size = 3
		self.convolution = np.zeros(60)

		self.wLayout = pg.LayoutWidget()
		self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

		self.wSobelSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSobelSizeSlider.setMinimum(1)
		self.wSobelSizeSlider.setMaximum(3)
		self.wSobelSizeSlider.setSliderPosition(2)

		self.wMinLengthSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wMinLengthSlider.setMinimum(3)
		self.wMinLengthSlider.setMaximum(10)
		self.wMinLengthSlider.setSliderPosition(3)

		self.wSNRSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wSNRSlider.setMinimum(1)
		self.wSNRSlider.setMaximum(100)
		self.wSNRSlider.setSliderPosition(20)

		self.wNoisePercSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.wNoisePercSlider.setMinimum(1)
		self.wNoisePercSlider.setMaximum(99)
		self.wNoisePercSlider.setSliderPosition(10)

		self.wHistPlot = pg.PlotWidget(title='Angle Histogram')
		self.wHistPlot.setXRange(0,180)
		self.wHistPlot.hideAxis('left')

		self.wConvPlot = pg.PlotWidget(title='Convolution with Comb Function')
		self.wConvPlot.setXRange(0,60)
		self.wConvPlot.hideAxis('left')

		self.wStd = QtGui.QLabel('')

		self.wLayout.addWidget(QtGui.QLabel('Size:'),0,0)
		self.wLayout.addWidget(self.wSobelSizeSlider,0,1)

		self.wLayout.addWidget(self.wHistPlot,4,0,4,4)
		self.wLayout.addWidget(self.wConvPlot,8,0,4,4)
		self.wLayout.addWidget(QtGui.QLabel('Shifted St. Dev.:'),12,0)
		self.wLayout.addWidget(self.wStd,12,1)

		self.wSobelSizeSlider.valueChanged.connect(self.update_view)

		self.update_view()

	def to_dict(self):
		d = super(SobelFilter,self).to_dict()
		d['sobel'] = {
			'ksize': self.sobel_size
		}
		d['size_tick'] = int(self.wSobelSizeSlider.value())
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(SobelFilter,cls).from_dict(d,img_item)
		obj.sobel_size = d['sobel']['ksize']

		obj.wSobelSizeSlider.setSliderPosition(d['size_tick'])
		obj.update_image()
		obj.widget().hide()

		return obj

	def update_image(self):
		self.sobel_size = 2*int(self.wSobelSizeSlider.value())+1

		self.dx = cv2.Sobel(self.mod_in.image(),ddepth=cv2.CV_64F,dx=1,dy=0,ksize=self.sobel_size)
		self.dy = cv2.Sobel(self.mod_in.image(),ddepth=cv2.CV_64F,dx=0,dy=1,ksize=self.sobel_size)

		self.properties['theta'] = np.arctan2(self.dy,self.dx)*180/np.pi
		self.properties['magnitude'] = np.sqrt(self.dx**2+self.dy**2)

		self.properties['angle_histogram'] = {}
		self.properties['angle_histogram']['y'],self.properties['angle_histogram']['x'] = np.histogram(
			self.properties['theta'].flatten(),
			weights=self.properties['magnitude'].flatten(),
			bins=np.linspace(0,180,180),
			density=True)

		comb = np.zeros(120)
		comb[0] = 1
		comb[60] = 1
		comb[-1] = 1
		self.convolution = sc.signal.convolve(self.properties['angle_histogram']['y'],comb,mode='valid')
		self.convolution = self.convolution/sum(self.convolution)
		cos = np.average(np.cos(np.arange(len(self.convolution))*2*np.pi/60),weights=self.convolution)
		sin = np.average(np.sin(np.arange(len(self.convolution))*2*np.pi/60),weights=self.convolution)
		self.periodic_mean = np.round((np.arctan2(-sin,-cos)+np.pi)*60/2/np.pi).astype(int)
		self.convolution = np.roll(self.convolution,30-self.periodic_mean)
		self.periodic_var = np.average((np.arange(len(self.convolution))-30)**2,weights=self.convolution)

		self.properties['convolution'] = self.convolution
		self.properties['periodic_var'] = self.periodic_var

	def update_view(self):
		self.update_image()
		self.img_item.setImage(self.properties['magnitude'])
		self.wConvPlot.clear()
		self.wConvPlot.plot(range(len(self.convolution)),self.convolution)
		self.wConvPlot.addLine(x=30)
		self.wConvPlot.addLine(x=30-np.sqrt(self.periodic_var),pen=pg.mkPen(dash=[3,5]))
		self.wConvPlot.addLine(x=30+np.sqrt(self.periodic_var),pen=pg.mkPen(dash=[3,5]))
		self.wHistPlot.clear()
		self.wHistPlot.plot(
			self.properties['angle_histogram']['x'],
			self.properties['angle_histogram']['y'],
			stepMode=True,
			fillLevel=0,
			brush=(0,0,255,150))
		self.wStd.setNum(np.sqrt(self.periodic_var))

		return self.properties

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Sobel Filter'

class ImageItemCenters(pg.ImageItem):
	def __init__(self,mod,img):
		super(ImageItemCenters,self).__init__()
		self.mod = mod
		self.start_img = img.copy()
		kern = (np.ones((2,2))*255).astype(np.uint8)
		self.setDrawKernel(kern, mask=None, center=(int(1),int(1)), mode='set')

	def drawAt(self,pos,ev=None):
		pos = [int(pos.x()), int(pos.y())]
		self.drawCircle(pos)
		self.mod.properties['centers'].append(pos)
		self.updateImage()
		self.mod.update_view()

	def drawCircle(self,pos,radius=5):
		a, b = pos[0],pos[1]
		nx,ny = self.image.shape
		radius = 5

		x,y = np.ogrid[-a:nx-a, -b:ny-b]
		mask = x*x + y*y <= radius**2

		self.image[mask] = 255

	def removeCenter(self):
		if len(self.mod.properties['centers']) > 0:
			del self.mod.properties['centers'][-1]
			self.image = self.start_img.copy()
			for pos in self.mod.properties['centers']:
				self.drawCircle(pos)
			self.updateImage()
			self.mod.update_view()

	def mouseDragEvent(self,ev):
		pass

class ImageItemMask(pg.ImageItem):
	def __init__(self,mod):
		super(ImageItemMask,self).__init__()
		self.mod = mod
		kern = (np.ones((2,2))*255).astype(np.uint8)
		self.setDrawKernel(kern, mask=None, center=(int(1),int(1)), mode='set')

	def drawAt(self,pos,ev=None):
		self.mod.erase(pos,radius=self.mod.eraser_size)

	def hoverEvent(self,ev):
		super(ImageItemMask,self).hoverEvent(ev)
		self.mod.hover_mask = np.zeros_like(self.mod.hover_mask,dtype=np.uint8)
		if self.mod._item != None and not ev.isExit():
			if self.mod._item['layer']=='erase':
				pos = ev.pos()
				nx,ny = self.mod.hover_mask.shape
				a, b = int(pos.x()), int(pos.y())
				cv2.circle(self.mod.hover_mask,(b,a),self.mod.eraser_size,1,3)

		slow_update(self.mod.update_view())

if __name__ == '__main__':
	if len(sys.argv) > 1:
		mode = sys.argv[1]
	else:
		mode = 'local'
	if mode not in ['nanohub','local']:
		mode = 'local'
	app = QtGui.QApplication([])
	img_analyzer = GSAImage(mode=mode)
	img_analyzer.run()
	sys.exit(app.exec_())
