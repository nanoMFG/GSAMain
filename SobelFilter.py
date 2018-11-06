import cv2
import Modification
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import scipy as sc

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
