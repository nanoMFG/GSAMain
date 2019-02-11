from __future__ import division
import numpy as np
import scipy as sc
import cv2, sys, time, json, copy, subprocess, os
from skimage import transform
from PyQt5 import QtGui, QtCore
import pyqtgraph as pg
from gresq.database import sample, preparation_step, dal, Base
from sqlalchemy import String, Integer, Float, Numeric
from gresq.config import config
from gresq.csv2db import build_db
from gresq.forge2db import build_db
from GSAQuery import GSAQuery
from GSAImage import GSAImage

class GSADashboard:
	def __init__(self,mode='local'):
		self.tabs = QtGui.QTabWidget()
		
		self.query_tab = GSAQuery()
		self.image_tab = GSAImage().widget()
		self.submit_tab =  QtGui.QWidget()
		self.raman_tab =  QtGui.QWidget()

		self.tabs.addTab(self.query_tab,'Query')
		self.tabs.addTab(self.image_tab,'SEM')
		self.tabs.addTab(self.raman_tab,'Raman')
		self.tabs.addTab(self.submit_tab,'Submit')

	def run(self):
		self.tabs.show()

if __name__ == '__main__':
	dal.init_db(config['development'])
	Base.metadata.drop_all(bind=dal.engine)
	Base.metadata.create_all(bind=dal.engine)
	with dal.session_scope() as session:
		# build_db(session,os.path.join(os.getcwd(),'data'))
		build_db(session)
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