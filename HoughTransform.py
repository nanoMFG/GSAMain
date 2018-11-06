import cv2
import Modification
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
from skimage import transform

class HoughTransform(Modification):
    def __init__(self, mod_in, img_item, properties={}):
        super(HoughTransform, self).__init__(mod_in, img_item, properties)
        self.inv_img = 255 - self.mod_in.image()
        self.img_out = self.mod_in.image()
        self.wLayout = pg.LayoutWidget()
        self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)
        self.thresh_tick = 100
        self.min_angle = 10
        self.min_dist = 9
        self.line_length = 50
        self.line_gap = 10
        self.hspace, self.angles, self.distances = transform.hough_line(self.inv_img)

        self.properties['hough_transform'] = {
            'angles': self.angles,
            'distances': self.distances,
            'hspace': self.hspace
        }

        self.wImgBox = pg.GraphicsLayoutWidget()
        self.wImgBox_VB = self.wImgBox.addViewBox(row=1, col=1)
        self.wHough = pg.ImageItem()
        # self.wHough.setImage(self.hspace,levels=(0,255))
        self.wImgBox_VB.addItem(self.wHough)
        # self.wImgBox_VB.setAspectLocked(True)
        # self.wImgBox_VB.setMouseEnabled(False,False)

        self.wHistPlot = pg.PlotWidget(title='Angle Histogram')
        self.wHistPlot.setXRange(0, 180)
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

        self.wLayout.addWidget(QtGui.QLabel('Minimum Angle:'), 0, 0)
        self.wLayout.addWidget(self.wMinAngleSlider, 0, 1)
        self.wLayout.addWidget(QtGui.QLabel('Minimum Distance:'), 1, 0)
        self.wLayout.addWidget(self.wMinDistSlider, 1, 1)
        self.wLayout.addWidget(QtGui.QLabel('Threshold:'), 2, 0)
        self.wLayout.addWidget(self.wThreshSlider, 2, 1)
        self.wLayout.addWidget(self.wImgBox, 3, 0, 2, 2)
        self.wLayout.addWidget(QtGui.QLabel('Minimum Line Length:'), 5, 0)
        self.wLayout.addWidget(self.wLengthSlider, 5, 1)
        self.wLayout.addWidget(QtGui.QLabel('Minimum Gap Length:'), 6, 0)
        self.wLayout.addWidget(self.wGapSlider, 6, 1)
        self.wLayout.addWidget(self.wHistPlot, 7, 0, 2, 2)

        self.wThreshSlider.valueChanged.connect(self.update_view)
        self.wMinAngleSlider.valueChanged.connect(self.update_view)
        self.wMinDistSlider.valueChanged.connect(self.update_view)
        self.wLengthSlider.valueChanged.connect(self.update_view)
        self.wGapSlider.valueChanged.connect(self.update_view)

    def to_dict(self):
        d = super(HoughTransform, self).to_dict()
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
    def from_dict(cls, d, img_item):
        obj = super(HoughTransform, obj).from_dict(d, img_item)
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
        self.threshold = int(np.max(self.hspace) * self.wThreshSlider.value() / 200)
        self.min_angle = int(self.wMinAngleSlider.value())
        self.min_dist = int(self.wMinDistSlider.value())
        self.line_length = int(self.wLengthSlider.value())
        self.line_gap = int(self.wGapSlider.value())

        accum, angles, dists = transform.hough_line_peaks(
            self.hspace,
            self.angles,
            self.distances,
            min_distance=self.min_dist,
            min_angle=self.min_angle,
            threshold=self.threshold)

        # angle_diffs = []
        # for i,a1 in enumerate(angles):
        #   for j,a2 in enumerate(angles):
        #     if i < j:
        #       angle_diffs.append(abs(a1-a2)*180)

        y, x = np.histogram(np.array(angles) * 180, bins=np.linspace(0, 180, 180))
        self.wHistPlot.clear()
        self.wHistPlot.plot(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))

        lines = transform.probabilistic_hough_line(
            self.inv_img,
            threshold=self.threshold,
            line_length=self.line_length,
            line_gap=self.line_gap)

        self.bgr_hough = 255 - np.round(self.hspace / np.max(self.hspace) * 255).astype(np.uint8)
        self.bgr_hough = cv2.cvtColor(self.bgr_hough, cv2.COLOR_GRAY2BGR)

        for a, d in zip(angles, dists):
            angle_idx = np.nonzero(a == self.angles)[0]
            dist_idx = np.nonzero(d == self.distances)[0]
            cv2.circle(self.bgr_hough, center=(angle_idx, dist_idx), radius=5, color=(0, 0, 255), thickness=-1)

        self.bgr_img = self.mod_in.image()
        self.bgr_img = cv2.cvtColor(self.bgr_img, cv2.COLOR_GRAY2BGR)

        for p1, p2 in lines:
            cv2.line(bgr_img, p1, p2, color=(0, 0, 255), thickness=2)

    def update_view(self):
        self.wHough.setImage(self.bgr_hough)
        self.img_item.setImage(self.bgr_img)

        return self.properties

    def widget(self):
        return self.wLayout

    def name(self):
        return 'Hough Transform'
