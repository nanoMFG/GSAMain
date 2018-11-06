import Modification
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

class Erase(Modification):
    def __init__(self, mod_in, img_item, properties={}):
        super(Erase, self).__init__(mod_in, img_item, properties)
        self.img_out = self.mod_in.image()
        self.eraser_size = 10
        self.wLayout = pg.LayoutWidget()
        self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

        self.wImgBox = pg.GraphicsLayoutWidget()
        self.wImgBox_VB = self.wImgBox.addViewBox(row=1, col=1)
        self.wImgROI = pg.ImageItem()
        self.wImgROI.setImage(self.img_out, levels=(0, 255))
        self.wImgBox_VB.addItem(self.wImgROI)
        self.wImgBox_VB.setAspectLocked(True)

        self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.wSizeSlider.setMinimum(1)
        self.wSizeSlider.setMaximum(100)
        self.wSizeSlider.setSliderPosition(self.eraser_size)

        kern = (np.ones((self.eraser_size, self.eraser_size)) * 255).astype(np.uint8)
        self.wImgROI.setDrawKernel(kern, mask=None, center=(int(self.eraser_size / 2), int(self.eraser_size / 2)),
                                   mode='set')
        self.wSizeSlider.valueChanged.connect(self.update_view)

        self.wLayout.addWidget(QtGui.QLabel('Eraser Size:'), 0, 0)
        self.wLayout.addWidget(self.wSizeSlider, 0, 1)
        self.wLayout.addWidget(self.wImgBox, 1, 0, 4, 4)

    def to_dict(self):
        d = super(Erase, self).to_dict()
        d['eraser_size'] = self.eraser_size
        d['erased_image'] = self.img_out.tolist()
        return d

    @classmethod
    def from_dict(cls, d, img_item):
        obj = super(Erase, cls).from_dict(d, img_item)
        obj.eraser_size = d['eraser_size']
        obj.wSizeSlider.setSliderPosition(d['eraser_size'])
        obj.wImgROI.setImage(np.array(d['erased_image']), levels=(0, 255))
        obj.update_image()

        obj.widget().hide()
        return obj

    def update_image(self):
        self.eraser_size = int(self.wSizeSlider.value())
        kern = (np.ones((self.eraser_size, self.eraser_size)) * 255).astype(np.uint8)
        self.wImgROI.setDrawKernel(kern, mask=None, center=(int(self.eraser_size / 2), int(self.eraser_size / 2)),
                                   mode='set')
        self.img_out = self.wImgROI.image

    def widget(self):
        return self.wLayout

    def name(self):
        return 'Erase'
