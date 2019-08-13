from __future__ import division
import numpy as np
import scipy as sc
import cv2
import sys
import time
import json
import copy
import subprocess
import os
import argparser
from skimage import transform
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
from gresq.database import sample, preparation_step, dal, Base
from sqlalchemy import String, Integer, Float, Numeric
from gresq.config import config
from gresq.csv2db import build_db
from gresq.csv2db import build_db
from gresq.forge2db import build_db
from GSAQuery import GSAQuery
from GSAImage import GSAImage
from GSASubmit import GSASubmit
# from GSARaman import GSARaman
from GSAOscm import GSAOscm


class GSADashboard(QtGui.QTabWidget):
    def __init__(self, parent=None, mode='local', box_config_path=None, api_info={}):
        super(GSADashboard, self).__init__(parent=parent)

        self.query_tab = GSAQuery()
        self.image_tab = GSAImage(mode=mode).widget()
        self.submit_tab = GSASubmit(mode=mode,box_config_path=box_config_path)
        self.oscm_tab = GSAOscm(server_instance='prod')
        self.submit_tab.preparation.oscm_signal.connect(lambda: self.setCurrentWidget(self.oscm_tab))

        self.addTab(self.query_tab, 'Query')
        self.addTab(self.image_tab, 'SEM Analysis')
        self.addTab(self.submit_tab, 'Submit')
        self.addTab(self.oscm_tab, 'OSCM')


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--nanohub', action = 'store_true', default = False, help='Configure for nanohub.')
	parser.add_argument('--release_db', action = 'store_true', default = False, help='Configure database for release version.')
	parser.add_argument('--uid', default = -1, type = int, help='User ID, necessary for submitting/editing database.')
	parser.add_argument('--box_config_path', default = "../box_config.json", type = str, help='Path to box config.')

	kwargs = vars(parser.parse_args())


    dal.init_db(config['development'])
    # Base.metadata.drop_all(bind=dal.engine)
    # Base.metadata.create_all(bind=dal.engine)
    # with dal.session_scope() as session:
    #     build_db(session)
    if kwargs['nanohub'] == True:
    	mode = 'nanohub'
    	with open(os.path.join(os.environ['SESSIONDIR'],'resources'),'r') as f:
    		for line in f.readlines():
    			words = line.split()
    			if words[0] == 'sessionid':
    				sessionnum = words[1]
    			if words[0] == 'session_token':
    				sessiontoken = words[1]

    	api_info = {'sessionnum':sessionnum,'sessiontoken':sessiontoken}
    	if kwargs['uid'] != -1:
    		api_info['id'] = str(kwargs['uid'])

    box_config_path = kwargs['box_config_path']

    app = QtGui.QApplication([])
    dashboard = GSADashboard(mode=mode,box_config_path=box_config_path,api_info=api_info)
    dashboard.show()
    sys.exit(app.exec_())
