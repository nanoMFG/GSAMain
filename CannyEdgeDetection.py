import cv2
import Modification
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
class CannyEdgeDetection(Modification):
    def __init__(self, mod_in, img_item, properties={}):
        super(CannyEdgeDetection, self).__init__(mod_in, img_item, properties)

        self.low_thresh = int(max(self.mod_in.image().flatten()) * .1)
        self.high_thresh = int(max(self.mod_in.image().flatten()) * .4)
        self.gauss_size = 5
        self.wToolBox = pg.LayoutWidget()
        self.wToolBox.layout.setAlignment(QtCore.Qt.AlignTop)

        self.wGaussEdit = QtGui.QLineEdit(str(self.gauss_size))
        self.wGaussEdit.setValidator(QtGui.QIntValidator(3, 51))
        self.wGaussEdit.setFixedWidth(60)

        self.wLowSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.wLowSlider.setMinimum(0)
        self.wLowSlider.setMaximum(255)
        self.wLowSlider.setSliderPosition(int(self.low_thresh))
        self.wLowEdit = QtGui.QLineEdit(str(self.low_thresh))
        self.wLowEdit.setFixedWidth(60)
        self.wLowEdit.setValidator(QtGui.QIntValidator(0, 255))

        self.wHighSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.wHighSlider.setMinimum(0)
        self.wHighSlider.setMaximum(255)
        self.wHighSlider.setSliderPosition(int(self.high_thresh))
        self.wHighEdit = QtGui.QLineEdit(str(self.high_thresh))
        self.wHighEdit.setFixedWidth(60)
        self.wHighEdit.setValidator(QtGui.QIntValidator(0, 255))

        self.wGaussEdit.returnPressed.connect(self._update_sliders)
        self.wLowSlider.sliderReleased.connect(self._update_texts)
        self.wLowSlider.sliderMoved.connect(self._update_texts)
        self.wLowEdit.returnPressed.connect(self._update_sliders)
        self.wHighSlider.sliderReleased.connect(self._update_texts)
        self.wHighSlider.sliderMoved.connect(self._update_texts)
        self.wHighEdit.returnPressed.connect(self._update_sliders)

        self.wToolBox.addWidget(QtGui.QLabel('Gaussian Size'), 0, 0)
        self.wToolBox.addWidget(QtGui.QLabel('Low Threshold'), 1, 0)
        self.wToolBox.addWidget(QtGui.QLabel('High Threshold'), 3, 0)
        self.wToolBox.addWidget(self.wGaussEdit, 0, 1)
        self.wToolBox.addWidget(self.wLowEdit, 1, 1)
        self.wToolBox.addWidget(self.wHighEdit, 3, 1)
        self.wToolBox.addWidget(self.wLowSlider, 2, 0, 1, 2)
        self.wToolBox.addWidget(self.wHighSlider, 4, 0, 1, 2)

    def to_dict(self):
        d = super(CannyEdgeDetection, self).to_dict()
        d['canny_inputs'] = {
            'low_threshold': self.low_thresh,
            'high_threshold': self.high_thresh,
            'gaussian_size': self.gauss_size
        }
        return d

    @classmethod
    def from_dict(cls, d, img_item):
        obj = super(CannyEdgeDetection, cls).from_dict(d, img_item)
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
        self.img_out = cv2.GaussianBlur(self.mod_in.image(), (self.gauss_size, self.gauss_size), 0)
        self.img_out = 255 - cv2.Canny(self.img_out, self.low_thresh, self.high_thresh, L2gradient=True)

    def widget(self):
        return self.wToolBox
