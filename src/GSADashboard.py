from __future__ import division
import sys
import os
import argparse
from PyQt5 import QtGui
from gresq.database import dal
from gresq.config import config
from GSAQuery import GSAQuery
from GSAImage import GSAImage
from GSASubmit import GSASubmit
# from GSARaman import GSARaman
from GSAOscm import GSAOscm


class GSADashboard(QtGui.QTabWidget):
	def __init__(self, parent=None, mode='local',box_config_path=None, privileges={'read':True,'write':False,'validate':False},test=False):
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


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--nanohub', action = 'store_true', default = False, help='Configure for nanohub.')
	parser.add_argument('--test', action = 'store_true', default = False, help='Test configuration.')
	parser.add_argument('--release_db', action = 'store_true', default = False, help='Configure database for release version.')
	parser.add_argument('--box_config_path', default = "../box_config.json", type = str, help='Path to box config.')

	kwargs = vars(parser.parse_args())

	admin_group = 31595
	submit_group = -1

	if kwargs['nanohub'] == True:
		mode = 'nanohub'
		groups = os.getgroups()
		if admin_group in groups:
			privileges = {'read':True,'write':True,'validate':True}
		elif submit_group in groups:
			privileges = {'read':True,'write':True,'validate':False}
	else:
		mode = 'local'
		privileges = {'read':True,'write':False,'validate':True}



	dal.init_db(config['development'],privileges=privileges)
	box_config_path = os.path.abspath(kwargs['box_config_path'])

	app = QtGui.QApplication([])
	dashboard = GSADashboard(mode=mode,box_config_path=box_config_path,privileges=privileges,test=kwargs['test'])
	dashboard.show()
	sys.exit(app.exec_())
