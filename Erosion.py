import cv2
import Modification
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

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
	def from_dict(self,d,img_item):
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
