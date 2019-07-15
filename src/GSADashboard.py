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
    def __init__(self, parent=None, mode='local', box_config_path=None):
        super(GSADashboard, self).__init__(parent=parent)

        self.query_tab = GSAQuery()
        self.image_tab = GSAImage(mode=mode).widget()
        self.submit_tab = GSASubmit(mode=mode, box_config_path=box_config_path)
        self.oscm_tab = GSAOscm(server_instance='dev')
        self.submit_tab.preparation.oscm_signal.connect(lambda: self.setCurrentWidget(self.oscm_tab))

        self.addTab(self.query_tab, 'Query')
        # self.addTab(self.image_tab, 'SEM Analysis')
        self.addTab(self.submit_tab, 'Submit')
        self.addTab(self.oscm_tab, 'OSCM')


if __name__ == '__main__':
    dal.init_db(config['development'])
    Base.metadata.drop_all(bind=dal.engine)
    Base.metadata.create_all(bind=dal.engine)
    with dal.session_scope() as session:
        build_db(session)
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'local'
    if mode not in ['nanohub', 'local']:
        mode = 'local'

    if len(sys.argv) > 2:
        box_config_path = sys.argv[2]
    else:
        box_config_path = "../box_config.json"

    app = QtGui.QApplication([])
    dashboard = GSADashboard(mode=mode, box_config_path=box_config_path)
    dashboard.show()
    sys.exit(app.exec_())
