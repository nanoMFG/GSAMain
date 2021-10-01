from __future__ import division
import subprocess
import os
from PyQt5 import QtGui, QtCore, QtWidgets
from gresq.dashboard.submit import GSASubmit
from gresq.dashboard.query import GSAQuery

# from GSARaman import GSARaman
from gresq.dashboard.oscm import GSAOscm
from gresq.util.util import ConfigParams
from gresq.util.icons import Icon

class GSADashboard(QtWidgets.QMainWindow):
    """
    Main window containing the GSAImage widget. Adds menu bar / tool bar functionality.
    """
    def __init__(
        self,
        mode="local",
        box_config_path=None,
        privileges={"read": True, "write": False, "validate": False},
        test=False,
        repo_dir='.',
        *args,
        **kwargs
        ):
        super(GSADashboard,self).__init__(*args,**kwargs)

        self.config = ConfigParams(
            box_config_path=box_config_path,
            mode=mode,
            read=privileges['read'],
            write=privileges['write'],
            validate=privileges['validate'],
            test=test)
        self.repo_dir = repo_dir

        # building main menu
        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)

        aboutAction = QtGui.QAction("&About",self)
        aboutAction.setIcon(Icon('info.svg'))
        aboutAction.triggered.connect(self.showAboutDialog)

        helpMenu = mainMenu.addMenu('&Help')
        helpMenu.addAction(aboutAction)

        self.query_tab = GSAQuery(config=self.config)
        self.submit_tab = GSASubmit(config=self.config)
        self.oscm_tab = GSAOscm(server_instance="prod")
        self.submit_tab.preparation.oscm_signal.connect(
            lambda: self.setCurrentWidget(self.oscm_tab)
        )

        self.mainWidget = QtGui.QTabWidget()
        self.mainWidget.addTab(self.query_tab, "Query")
        self.mainWidget.addTab(self.submit_tab, "Submit")
        self.mainWidget.addTab(self.oscm_tab, "OSCM")
        self.mainWidget.addTab(self.query_tab, "Query_2_0")
        self.mainWidget.addTab(self.submit_tab, "Submit_2_0")

        self.setCentralWidget(self.mainWidget)


    def showAboutDialog(self):
        about_dialog = QtWidgets.QMessageBox(self)
        about_dialog.setText("About This Tool")
        about_dialog.setWindowModality(QtCore.Qt.WindowModal)
        copyright_path = os.path.join(self.repo_dir,'COPYRIGHT')
        print(f"okay:{copyright_path}")
        if os.path.isfile(copyright_path):
            with open(copyright_path,'r') as f:
                copyright = f.read()
                print(f"hey:{copyright}")
        else:
            copyright = ""

        version_path =  os.path.join(self.repo_dir,'VERSION')
        if os.path.isfile(version_path):
            with open(os.path.join(self.repo_dir,'VERSION'),'r') as f:
                version = f.read()
        else:
            version = ""

        # Needs text
        about_text = "Version: %s \n\n"%version
        about_text += copyright

        about_dialog.setInformativeText(about_text)
        about_dialog.exec()


# class GSADashboard(QtGui.QTabWidget):
#     def __init__(
#         self,
#         parent=None,
#         mode="local",
#         box_config_path=None,
#         privileges={"read": True, "write": False, "validate": False},
#         test=False,
#     ):
#         super(GSADashboard, self).__init__(parent=parent)
#         self.config = ConfigParams(
#             box_config_path=box_config_path,
#             mode=mode,
#             read=privileges['read'],
#             write=privileges['write'],
#             validate=privileges['validate'],
#             test=test)
#         self.query_tab = GSAQuery(config=self.config)
#         self.submit_tab = GSASubmit(config=self.config)
#         self.oscm_tab = GSAOscm(server_instance="prod")
#         self.submit_tab.preparation.oscm_signal.connect(
#             lambda: self.setCurrentWidget(self.oscm_tab)
#         )

#         self.addTab(self.query_tab, "Query")
#         self.addTab(self.submit_tab, "Submit")
#         self.addTab(self.oscm_tab, "OSCM")
