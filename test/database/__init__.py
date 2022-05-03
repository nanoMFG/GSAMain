import os

from gresq.config import Config
from grdb.database.v1_1_0 import dal

#config_prefix = os.getenv('GRESQ_TEST_CONFIG_PREFIX', 'TEST_DATABASE') 
#config_suffix = os.getenv('GRESQ_TEST_CONFIG_SUFFIX', '_ADMIN')
config_prefix = 'TEST_DATABASE'
config_suffix = '_ADMIN'

#print("HHHHHHEEEEEYYYYY")
conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
#test_session = dal.Session()
