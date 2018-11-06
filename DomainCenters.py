import ImageItemCenters
import Modification
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

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
