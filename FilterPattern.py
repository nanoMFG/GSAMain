import cv2
import GSAImage
import ImageItemMask
import Modification
import numpy as np
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
import sys

class FilterPattern(Modification):
    def __init__(self, mod_in, img_item, properties={}):
        super(FilterPattern, self).__init__(mod_in, img_item, properties)
        self.roi_size = 20
        self.scale = 1
        self.layer_list = []
        self.hover_mask = np.zeros_like(self.mod_in.image()).astype(np.uint8)
        self._item = None

        self.wLayout = pg.LayoutWidget()
        self.wLayout.layout.setAlignment(QtCore.Qt.AlignTop)

        self.wFilterList = QtGui.QListWidget()
        self.wFilterList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.wAdd = QtGui.QPushButton('Add Filter')
        self.wRemove = QtGui.QPushButton('Remove Layer')
        self.wErase = QtGui.QPushButton('Add Erase')

        self.wImgBox = pg.GraphicsLayoutWidget()
        self.wImgBox_VB = self.wImgBox.addViewBox(row=1, col=1)
        self.wImgROI = ImageItemMask(self)
        self.wImgROI.setImage(self.img_item.image, levels=(0, 255))
        self.wImgBox_VB.addItem(self.wImgROI)
        self.wImgBox_VB.setAspectLocked(True)

        self.wComboBox = pg.ComboBox()
        self.wComboBox.addItem('TM_SQDIFF')
        self.wComboBox.addItem('TM_SQDIFF_NORMED')
        self.wComboBox.addItem('TM_CCORR')
        self.wComboBox.addItem('TM_CCORR_NORMED')
        self.wComboBox.addItem('TM_CCOEFF')
        self.wComboBox.addItem('TM_CCOEFF_NORMED')

        self.method_dict = {
            'TM_SQDIFF': cv2.TM_SQDIFF,
            'TM_SQDIFF_NORMED': cv2.TM_SQDIFF_NORMED,
            'TM_CCORR': cv2.TM_CCORR,
            'TM_CCORR_NORMED': cv2.TM_CCORR_NORMED,
            'TM_CCOEFF': cv2.TM_CCOEFF,
            'TM_CCOEFF_NORMED': cv2.TM_CCOEFF_NORMED
        }

        self.wThreshSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.wThreshSlider.setMinimum(1)
        self.wThreshSlider.setMaximum(1000)
        self.wThreshSlider.setSliderPosition(100)

        self.wSizeSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.wSizeSlider.setMinimum(2)
        self.wSizeSlider.setMaximum(50)
        self.wSizeSlider.setSliderPosition(5)

        self.wFilterAreaLabel = QtGui.QLabel('')
        self.wFilterScaleLabel = QtGui.QLabel('')

        self.wLayout.addWidget(QtGui.QLabel('Filter Method:'), 0, 0)
        self.wLayout.addWidget(self.wComboBox, 0, 1, 1, 3)
        self.wLayout.addWidget(QtGui.QLabel('Threshold:'), 1, 0)
        self.wLayout.addWidget(self.wThreshSlider, 1, 1, 1, 3)
        self.wLayout.addWidget(QtGui.QLabel('ROI Size:'), 2, 0)
        self.wLayout.addWidget(self.wSizeSlider, 2, 1, 1, 3)
        self.wLayout.addWidget(QtGui.QLabel('Area (um^2):'), 3, 0)
        self.wLayout.addWidget(self.wFilterAreaLabel, 3, 1)
        self.wLayout.addWidget(QtGui.QLabel('Scale (um/px):'), 4, 0)
        self.wLayout.addWidget(self.wFilterScaleLabel, 4, 1)
        self.wLayout.addWidget(self.wImgBox, 9, 0, 4, 4)
        self.wLayout.addWidget(self.wFilterList, 5, 0, 4, 3)
        self.wLayout.addWidget(self.wAdd, 5, 3)
        self.wLayout.addWidget(self.wRemove, 8, 3)
        self.wLayout.addWidget(self.wErase, 6, 3)

        self.wThreshSlider.valueChanged.connect(self.update_view)
        self.wComboBox.currentIndexChanged.connect(self.update_view)
        self.wSizeSlider.valueChanged.connect(self.update_view)
        self.wAdd.clicked.connect(self.addROI)
        self.wRemove.clicked.connect(self.removeLayer)
        self.wFilterList.itemSelectionChanged.connect(self.selectLayer)
        self.wErase.clicked.connect(self.addErase)

    def to_dict(self):
        d = super(FilterPattern, self).to_dict()
        d['layer_list'] = []
        for layer in self.layer_list:
            if layer['layer'] == 'filter':
                temp = {
                    'roi': layer['roi'].saveState(),
                    'threshold': layer['threshold'],
                    'layer': 'filter',
                    'mode': layer['mode']
                }
            else:
                temp = {
                    'layer': 'erase',
                }
            temp['mask'] = layer['mask'].copy().tolist()
            d['layer_list'].append(temp)
        return d

    @classmethod
    def from_dict(cls, d, img_item):
        obj = super(FilterPattern, cls).from_dict(d, img_item)
        for layer in d['layer_list']:
            if layer['layer'] == 'filter':
                obj.addROI()
                temp = obj.layer_list[-1]
                temp['roi'].setState(layer['roi'])
                temp['threshold'] = layer['threshold']
                temp['mode'] = layer['mode']
                obj.wSizeSlider.setSliderPosition(layer['roi']['size'][0])
                obj.wThreshSlider.setSliderPosition(layer['threshold'])
                obj.wComboBox.setValue(layer['mode'])
            elif layer['layer'] == 'erase':
                obj.addErase()
                temp = obj.layer_list[-1]
            temp['mask'] = np.array(layer['mask'])

        obj.update_image()
        obj.widget().hide()

        return obj

    def addErase(self):
        erase_dict = {
            'layer': 'erase',
            'mask': np.zeros_like(self.mod_in.image(), dtype=bool)
        }
        self.layer_list.append(erase_dict)
        self.wFilterList.addItem('Erase %d' % self.wFilterList.count())
        self.wFilterList.setCurrentRow(self.wFilterList.count() - 1)
        self.selectLayer()

    def erase(self, pos, radius=5):
        selection = self.wFilterList.selectedItems()
        if self._item['layer'] == 'erase' and len(selection) > 0:
            selection = selection[0]
            row = self.wFilterList.row(selection)
            if row == self.wFilterList.count() - 1:
                pos = [int(pos.x()), int(pos.y())]
                a, b = pos[0], pos[1]
                nx, ny = self._item['mask'].shape

                x, y = np.ogrid[-a:nx - a, -b:ny - b]
                mask = x * x + y * y <= radius ** 2
                self._item['mask'][mask] = True
                GSAImage.slow_update(self.update_view())

    def addROI(self):
        roi = pg.ROI(
            pos=(0, 0),
            size=(self.roi_size, self.roi_size),
            removable=True,
            pen=pg.mkPen(color='r', width=2),
            maxBounds=self.wImgROI.boundingRect(),
            scaleSnap=True,
            snapSize=2)
        roi.sigRegionChanged.connect(self.update_view)
        self.wImgBox_VB.addItem(roi)
        roi_dict = {
            'roi': roi,
            'threshold': 100,
            'mask': np.zeros_like(self.mod_in.image()),
            'layer': 'filter',
            'mode': None
        }
        self.layer_list.append(roi_dict)
        self.wFilterList.addItem('Filter %d' % self.wFilterList.count())
        self.wFilterList.setCurrentRow(self.wFilterList.count() - 1)
        self.selectLayer()

    def removeLayer(self):
        if len(self.layer_list) > 0:
            if self.layer_list[-1]['layer'] == 'filter':
                self.wImgBox_VB.removeItem(self.layer_list[-1]['roi'])
            del self.layer_list[-1]
            self.wFilterList.takeItem(self.wFilterList.count() - 1)
            if len(self.layer_list) > 0:
                self._item = self.layer_list[-1]
                self.wFilterList.setCurrentRow(self.wFilterList.count() - 1)
                self.selectLayer()
            else:
                self._item = None

    def selectLayer(self):
        selection = self.wFilterList.selectedItems()
        if len(selection) == 1:
            selection = selection[0]
            row = self.wFilterList.row(selection)
            self._item = self.layer_list[row]
            self.wImgROI.setImage(self.mod_in.image(), levels=(0, 255))
            if self._item['layer'] == 'filter':
                roi = self._item['roi']
                if self._item['mode'] != None:
                    self.wComboBox.setValue(self._item['mode'])
                self.wSizeSlider.setSliderPosition(int(roi.size()[0] / 2))
                self.wThreshSlider.setSliderPosition(self._item['threshold'])
            else:
                roi = None

            for r, ro in enumerate(self.layer_list):
                if ro['layer'] == 'filter':
                    if r != row:
                        ro['roi'].hide()
                    else:
                        ro['roi'].show()
        else:
            self._item = None

        self.update_view()

    def update_image(self):
        back_properties = self.back_properties()
        self.eraser_size = int(self.wSizeSlider.value())
        if 'scale' in back_properties.keys():
            self.scale = back_properties['scale']
        try:
            self.img_out = self.mod_in.image()
            self.roi_img = self.mod_in.image()
            self.roi_img = cv2.cvtColor(self.roi_img, cv2.COLOR_GRAY2BGR)
            if self._item != None:
                if self._item['layer'] == 'filter':
                    roi = self._item['roi']

                    roi_size = 2 * int(self.wSizeSlider.value())
                    if roi_size != roi.size()[0]:
                        roi.setSize([roi_size, roi_size])
                    self._item['mode'] = self.wComboBox.value()
                    self._item['threshold'] = self.wThreshSlider.value()

                    region = roi.getArrayRegion(self.mod_in.image(), self.wImgROI).astype(np.uint8)
                    x, y = region.shape
                    padded_image = cv2.copyMakeBorder(self.mod_in.image(), int(y / 2 - 1), int(y / 2), int(x / 2 - 1),
                                                      int(x / 2), cv2.BORDER_REFLECT_101)
                    res = cv2.matchTemplate(padded_image, region, self.method_dict[self._item['mode']])

                    if 'NORMED' in self._item['mode']:
                        maxVal = 1
                    else:
                        maxVal = res.flatten().max()
                    threshold = maxVal * np.logspace(-3, 0, 1000)[self._item['threshold'] - 1]
                    self._item['mask'] = np.zeros_like(self.img_out).astype(bool)
                    self._item['mask'][res < threshold] = True

                self.mask_total = np.zeros_like(self.img_out).astype(bool)
                selection = self.wFilterList.selectedItems()
                selection = selection[0]
                row = self.wFilterList.row(selection)
                for layer in self.layer_list[:row + 1]:
                    if layer['layer'] == 'filter':
                        self.mask_total[layer['mask']] = True
                    elif layer['layer'] == 'erase':
                        self.mask_total[layer['mask']] = False

                self.roi_img = self.mod_in.image()
                self.roi_img = cv2.cvtColor(self.roi_img, cv2.COLOR_GRAY2BGR)
                self.img_out[np.logical_not(self.mask_total)] = 255
                self.roi_img[self.mask_total, :] = [0, 0, 255]
                if self._item['layer'] == 'erase':
                    self.roi_img[self.hover_mask.astype(bool), :] = [0, 255, 0]

                self.properties['masked_area_um2'] = float(np.sum(self.mask_total) * self.scale ** 2)
                self.properties['mask_total'] = self.mask_total.tolist()
        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

    def update_view(self):
        self.update_image()
        if 'masked_area_um2' in self.properties.keys():
            self.wFilterAreaLabel.setNum(self.properties['masked_area_um2'])
        self.wFilterScaleLabel.setNum(self.scale)
        self.img_item.setImage(self.img_out, levels=(0, 255))
        self.wImgROI.setImage(self.roi_img)

        return self.properties

    def widget(self):
        return self.wLayout

    def name(self):
        return 'Filter Pattern'
