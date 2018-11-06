import cv2
import Modification
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

class FindContours(Modification):
    def __init__(self, mod_in, img_item, properties={}):
        super(FindContours, self).__init__(mod_in, img_item, properties)
        self.wLayout = pg.LayoutWidget()
        self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)
        self.img_inv = self.mod_in.image()
        self.img_inv[self.img_inv < 255] = 0
        self.img_inv = 255 - self.img_inv

        self.tol = 0.04
        self.wTolEdit = QtGui.QLineEdit(str(self.tol))
        self.wTolEdit.setValidator(QtGui.QDoubleValidator(0, 1, 3))
        self.wTolEdit.setFixedWidth(60)

        self.lowVert = 6
        self.wLowEdit = QtGui.QLineEdit(str(self.lowVert))
        self.wLowEdit.setValidator(QtGui.QIntValidator(3, 100))
        self.wLowEdit.setFixedWidth(60)

        self.highVert = 6
        self.wHighEdit = QtGui.QLineEdit(str(self.highVert))
        self.wHighEdit.setValidator(QtGui.QIntValidator(3, 100))
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
        for i, cnt in enumerate(self.contours):
            key = '%d Contour' % i
            self.contour_dict[key] = {}
            self.contour_dict[key]['index'] = i
            self.contour_dict[key]['list_item'] = QtGui.QListWidgetItem(key)
            self.contour_dict[key]['contour'] = cnt
            self.contour_dict[key]['area'] = cv2.contourArea(cnt, oriented=True)
            if abs(self.contour_dict[key]['area']) > self.contour_area_max:
                self.contour_area_max = abs(self.contour_dict[key]['area'])
        self.update_tol()

        self.wContourList.itemSelectionChanged.connect(self.update_view)
        self.wContourList.itemClicked.connect(self.update_view)
        self.wTolEdit.returnPressed.connect(self.update_tol)
        self.wLowEdit.returnPressed.connect(self.update_tol)
        self.wHighEdit.returnPressed.connect(self.update_tol)
        self.wThreshSlider.valueChanged.connect(self.update_tol)

        if len(self.contour_dict.keys()) > 0:
            self.wContourList.setCurrentItem(self.contour_dict['0 Contour']['list_item'])

        self.wLayout.addWidget(self.wContourList, 0, 0, 2, 1)
        self.wLayout.addWidget(QtGui.QLabel('Polygon Tolerance:'), 3, 0)
        self.wLayout.addWidget(self.wTolEdit, 3, 1)
        self.wLayout.addWidget(QtGui.QLabel('Vertex Tolerance:'), 4, 0)
        self.wLayout.addWidget(self.wLowEdit, 4, 1)
        self.wLayout.addWidget(self.wHighEdit, 4, 2)
        self.wLayout.addWidget(QtGui.QLabel('Contour Area Tolerance:'), 5, 0)
        self.wLayout.addWidget(self.wThreshSlider, 6, 0, 1, 3)

        self.update_view()

    def to_dict(self):
        d = super(FindContours, self).to_dict()
        d['line_tolerance'] = self.tol
        d['low_vertex_threshold'] = self.lowVert
        d['high_vertex_threshold'] = self.highVert
        d['contour_area_threshold'] = self.areaThresh
        d['threshold_slider_tick'] = self.wThreshSlider.value()
        d['contours'] = self.contours
        return d

    @classmethod
    def from_dict(cls, d, img_item):
        obj = super(FindContours, cls).from_dict(d, img_item)
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
            cv2.drawContours(self.img_out, [approx], 0, thickness=2, color=(0, 255, 0))

    def detect_poly(self, cnt):
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, self.tol * peri, True)
        return len(approx) >= self.lowVert and len(approx) <= self.highVert, approx

    def update_tol(self):
        self.tol = float(self.wTolEdit.text())
        self.lowVert = float(self.wLowEdit.text())
        self.highVert = float(self.wHighEdit.text())
        self.areaThresh = float(self.wThreshSlider.value()) / 100.
        self.wContourList.clear()
        for key in self.contour_dict.keys():
            cnt = self.contour_dict[key]['contour']
            area = self.contour_dict[key]['area']
            accept, approx = self.detect_poly(cnt)
            if accept and area < 0 and abs(area / self.contour_area_max) >= self.areaThresh:
                self.contour_dict[key]['list_item'] = QtGui.QListWidgetItem(key)
                self.wContourList.addItem(self.contour_dict[key]['list_item'])

    def widget(self):
        return self.wLayout

    def name(self):
        return 'Find Contours'