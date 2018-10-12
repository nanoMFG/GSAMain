from __future__ import division
import numpy as np
import scipy as sc
import cv2, sys, time, json, copy, subprocess, os
from skimage import transform
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

from GSAQuery import GSAQuery
from GSAImage import GSAImage

class GSADashboard:
	def __init__(self,mode='local'):
		self.tabs = QtGui.QTabWidget()
		
		self.query_tab =  GSAQuery().widget()
		self.image_tab =  GSAImage().widget()
		self.stats_tab =  QtGui.QWidget()
		self.submit_tab =  QtGui.QWidget()

		self.tabs.addTab(self.query_tab,'Query')
		self.tabs.addTab(self.image_tab,'Image')
		self.tabs.addTab(self.stats_tab,'Statistics')
		self.tabs.addTab(self.submit_tab,'Submit')

	def run(self):
		self.tabs.show()

if __name__ == '__main__':
  if len(sys.argv) > 1:
    mode = sys.argv[1]
  else:
    mode = 'local'
  if mode not in ['nanohub','local']:
    mode = 'local'
  app = QtGui.QApplication([])      
  dashboard = GSADashboard(mode=mode)
  dashboard.run()
  sys.exit(app.exec_())