from __future__ import division
import os
import sys
#sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'gsaimage','src'))
from PyQt5 import QtGui
from gresq.dashboard.submit import GSASubmit
from gresq.dashboard.query import GSAQuery
# from GSARaman import GSARaman
from gresq.dashboard.oscm import GSAOscm


class GSADashboard(QtGui.QTabWidget):
    def __init__(self, parent=None, mode='local',box_config_path=None,
                 privileges={'read':True,'write':False,'validate':False},test=False):
        super(GSADashboard, self).__init__(parent=parent)

        self.query_tab = GSAQuery(privileges=privileges)
        # self.image_tab = GSAImage(mode=mode).widget()
        self.submit_tab = GSASubmit(mode=mode,box_config_path=box_config_path,privileges=privileges)
        self.oscm_tab = GSAOscm(server_instance='prod')
        self.submit_tab.preparation.oscm_signal.connect(lambda: self.setCurrentWidget(self.oscm_tab))

        self.addTab(self.query_tab, 'Query')
        # self.addTab(self.image_tab, 'SEM Analysis')
        self.addTab(self.submit_tab, 'Submit')
        self.addTab(self.oscm_tab, 'OSCM')

        if test:
            self.submit_tab.test()
