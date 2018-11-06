import Modification
import numpy as np
from PyQt5 import QtCore
import pyqtgraph as pg

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
