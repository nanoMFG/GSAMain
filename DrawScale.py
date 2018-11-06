import Modification
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

class DrawScale(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(DrawScale,self).__init__(mod_in,img_item,properties)
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

		self.wLengthEdit = QtGui.QLineEdit(str(self.scale))
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
		if self.num_pixels != 0:
			self.properties['scale'] = self.properties['scale_length_um'] / self.properties['num_pixels']
		self.wScale.setText(str(self.properties['scale']))

	def widget(self):
		return self.wLayout

	def name(self):
		return 'Draw Scale'
