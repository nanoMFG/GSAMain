from __future__ import division
import sys
import os
import argparse
import logging
from PyQt5 import QtGui
from gresq.config import Config
from gresq.database import dal
from gresq.submit import GSASubmit
from gresq.GSAImage import GSAImage
from gresq.query import GSAQuery
# from GSARaman import GSARaman
from gresq.oscm import GSAOscm


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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nanohub', action = 'store_true', default = False,
                        help='Configure for nanohub.')
    parser.add_argument('--test', action = 'store_true', default = False,
                        help='Test configuration.')
    parser.add_argument('--release_db', action = 'store_true', default = False,
                        help='Configure database for release version.')
    parser.add_argument('--box_config_path', default = "../box_config.json", type = str,
                        help='Path to box config.')
    parser.add_argument('--db_config_path', default = '', type = str, help='Path to database config secrets.')
    parser.add_argument('--db_mode', default = "development", type = str,
                        help='Database mode: development, testing, or production')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    kwargs = vars(parser.parse_args())

    if kwargs['verbose']:
        logging.basicConfig(level=logging.DEBUG)

    admin_group = 31595
    submit_group = -1

    # Set configuration prefix to search for when setting db config
    db_debug = True
    db_config_prefix = None
    if kwargs['db_mode'].lower() == 'development':
        db_config_prefix = 'DEV_DATABASE'
    elif kwargs['db_mode'].lower() == 'production':
        db_config_prefix = 'PROD_DATABASE'
        db_debug = False
    elif kwargs['db_mode'] == 'testing':
        db_config_prefix = 'TEST_DATABASE'

    db_config_suffix = ''
    if kwargs['nanohub'] == True:
        mode = 'nanohub'
        groups = os.getgroups()
        if admin_group in groups:
            privileges = {'read':True,'write':True,'validate':True}
            db_config_suffix = '_ADMIN'
        elif submit_group in groups:
            privileges = {'read':True,'write':True,'validate':False}
            db_config_suffix = '_WRITE'
        else:
            privileges = {'read':True,'write':False,'validate':False}
            db_config_suffix = '_READ'
    else:
        mode = 'local'
        privileges = {'read':True,'write':False,'validate':True}

    #logging.debug(db_config_prefix)
    #logging.debug(kwargs['db_config_path'])
    db_conf = Config(prefix=db_config_prefix, suffix=db_config_suffix, debug=db_debug,
                     dbconfig_file=kwargs['db_config_path'])
    #logging.debug(db_conf.DATABASEURI)
    #logging.debug(db_conf.DATABASEARGS)


    dal.init_db(db_conf, privileges=privileges)

    box_config_path = os.path.abspath(kwargs['box_config_path'])

    app = QtGui.QApplication([])
    dashboard = GSADashboard(mode=mode,box_config_path=box_config_path,privileges=privileges,test=kwargs['test'])
    dashboard.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
