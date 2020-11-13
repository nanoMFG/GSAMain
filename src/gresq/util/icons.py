import logging
import os
import sys

from PyQt5 import QtGui, QtWidgets, QtCore

logger = logging.getLogger(__name__)

QG = QtGui
QW = QtWidgets
QC = QtCore

catalogue_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'icons_catalogue')

class Icon(QG.QIcon):
	def __init__(self,fileName,*args,**kwargs):
		path = os.path.join(catalogue_dir,fileName)
		super(Icon,self).__init__(path,*args,**kwargs)

class Browser(QW.QListView):
	def __init__(self,*args,**kwargs):
		super(Browser,self).__init__(*args,**kwargs)
		self.model = QG.QStandardItemModel()

		self.setViewMode(QW.QListView.IconMode)
		self.setModel(self.model)

		self.setGridSize(QC.QSize(64,64))
		self.setFlow(QW.QListView.LeftToRight)
		self.setResizeMode(QW.QListView.Adjust)

		self.buildModel()

	def buildModel(self):
		for f in sorted(os.listdir(catalogue_dir)):
			if f.split('.')[-1].upper() == 'SVG':
				item = QtGui.QStandardItem()
				item.setIcon(Icon(f))
				item.setText(f)

				self.model.appendRow(item)

if __name__ == "__main__":
	app = QW.QApplication([])
	browser = Browser()
	browser.show()

	sys.exit(app.exec_())