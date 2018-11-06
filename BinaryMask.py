import Modification

class BinaryMask(Modification):
	def __init__(self,mod_in,img_item,properties={}):
		super(BinaryMask,self).__init__(mod_in,img_item,properties)

	def to_dict(self):
		d = super(BinaryMask,self).to_dict()
		return d

	@classmethod
	def from_dict(cls,d,img_item):
		obj = super(BinaryMask,cls).from_dict(d,img_item)
		obj.update_image()
		return obj

	def name(self):
		return 'Binary Mask'

	def update_image(self):
		self.img_out = self.mod_in.image()
		self.img_out[self.img_out < 255] = 0
