import Modification
import numpy as np
class InitialImage(Modification):
  def name(self):
    return 'Initial Image'

  def to_dict(self):
    d = super(InitialImage, self).to_dict()
    d['img_out'] = self.img_out.tolist()
    return d

  @classmethod
  def from_dict(cls, d, img_item):
    obj = super(InitialImage, cls).from_dict(d, img_item)
    obj.set_image(np.asarray(d['img_out']))
    return obj