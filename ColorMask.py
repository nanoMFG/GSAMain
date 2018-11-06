import Modification
import numpy as np
import pyqtgraph as pg

class ColorMask(Modification):
  def __init__(self, mod_in, img_item, properties={}):
    super(ColorMask, self).__init__(mod_in, img_item, properties)
    self.img_mask = None
    self.img_hist = self.img_item.getHistogram()

    self.wHistPlot = None
    self.lrItem = None

    self.wHistPlot = pg.PlotWidget()
    self.wHistPlot.plot(*self.img_hist)
    self.wHistPlot.setXRange(0, 255)
    self.wHistPlot.hideAxis('left')

    self.lrItem = pg.LinearRegionItem((0, 255), bounds=(0, 255))
    self.lrItem.sigRegionChanged.connect(self.update_view)
    self.lrItem.sigRegionChangeFinished.connect(self.update_view)

    self.wHistPlot.addItem(self.lrItem)
    self.wHistPlot.setMouseEnabled(False, False)
    self.wHistPlot.setMaximumHeight(100)

  def to_dict(self):
    d = super(ColorMask, self).to_dict()
    d['img_mask'] = self.img_mask.tolist()
    d['LinearRegionItem'] = {'region': self.lrItem.getRegion()}
    return d

  @classmethod
  def from_dict(cls, d, img_item):
    obj = super(ColorMask, cls).from_dict(d, img_item)
    obj.img_mask = np.asarray(d['img_mask'])
    obj.lrItem.setRegion(d['LinearRegionItem']['region'])
    obj.update_image()
    obj.widget().hide()
    return obj

  def widget(self):
    return self.wHistPlot

  def update_image(self):
    minVal, maxVal = self.lrItem.getRegion()
    img = self.mod_in.image()
    self.img_mask = np.zeros_like(img)
    self.img_mask[np.logical_and(img > minVal, img < maxVal)] = 1
    self.img_out = img * self.img_mask + (1 - self.img_mask) * 255

  def name(self):
    return 'Color Mask'
