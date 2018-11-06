import cv2
import Modification
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

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
