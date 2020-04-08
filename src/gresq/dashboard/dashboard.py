from __future__ import division
from PyQt5 import QtGui, QtCore
from gresq.dashboard.submit import GSASubmit
from gresq.dashboard.query import GSAQuery

# from GSARaman import GSARaman
from gresq.dashboard.oscm import GSAOscm
from gresq.util.util import ConfigParams


class GSADashboard(QtGui.QTabWidget):
    def __init__(
        self,
        parent=None,
        mode="local",
        box_config_path=None,
        privileges={"read": True, "write": False, "validate": False},
        test=False,
    ):
        super(GSADashboard, self).__init__(parent=parent)
        self.config = ConfigParams(
            box_config_path=box_config_path,
            mode=mode,
            read=privileges['read'],
            write=privileges['write'],
            validate=privileges['validate'],
            test=test)
        self.query_tab = GSAQuery(config=self.config)
        self.submit_tab = GSASubmit(config=self.config)
        self.oscm_tab = GSAOscm(server_instance="prod")
        self.submit_tab.preparation.oscm_signal.connect(
            lambda: self.setCurrentWidget(self.oscm_tab)
        )

        self.addTab(self.query_tab, "Query")
        self.addTab(self.submit_tab, "Submit")
        self.addTab(self.oscm_tab, "OSCM")
