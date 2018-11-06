from PyQt5 import QtGui, QtCore
import numpy as np
import time

class Modification:
    def __init__(self, mod_in=None, img_item=None, properties={}):
        self.mod_in = mod_in
        self.img_item = img_item
        self.properties = properties
        if mod_in != None:
            self.img_out = self.mod_in.image()
        else:
            self.img_out = None

    def widget(self):
        return QtGui.QWidget()

    def image(self):
        return self.img_out.copy()

    def name(self):
        return 'Default Modification'

    def set_image(self, img):
        self.img_out = img.astype(np.uint8)

    def update_image(self):
        pass

    def update_view(self):
        self.update_image()
        self.img_item.setImage(self.img_out, levels=(0, 255))
        return self.properties

    def delete_mod(self):
        return self.mod_in

    def tolist(self):
        if self.mod_in != None:
            return self.mod_in.tolist() + [self]
        else:
            return [self]

    def back_traverse(self, n):
        if n != 0:
            if self.mod_in == None:
                raise IndexError('Index out of range (n = %d)' % n)
            elif n != 0:
                return self.mod_in.back_traverse(n - 1)
        elif n == 0:
            return self

    def root(self):
        if self.mod_in != None:
            return self.mod_in.root()
        else:
            return self

    def length(self):
        if self.mod_in != None:
            return self.mod_in.length() + 1
        else:
            return 1

    def back_properties(self):
        if self.mod_in != None:
            d = self.mod_in.back_properties()
            d.update(self.properties)
            return d
        else:
            d = {}
            d.update(self.properties)
            return d

    def to_dict(self):
        d = {}
        d['@module'] = self.__class__.__module__
        d['@class'] = self.__class__.__name__
        d['date'] = time.asctime()
        if self.mod_in != None:
            d['mod_in'] = self.mod_in.to_dict()
        else:
            d['mod_in'] = None
        d['properties'] = self.properties
        return d

    @classmethod
    def from_dict(cls, d, img_item):
        if d['mod_in'] != None:
            mod_in_dict = d['mod_in']
            mod_in_cls = globals()[mod_in_dict['@class']]
            mod_in = mod_in_cls.from_dict(mod_in_dict, img_item)
        else:
            mod_in = None
        return cls(mod_in, img_item, d['properties'])
