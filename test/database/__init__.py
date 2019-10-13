from gresq.config import Config
from gresq.database import dal

config_prefix = 'TEST_DATABASE'
config_suffix = '_ADMIN'

#print("HHHHHHEEEEEYYYYY")
conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
test_session = dal.Session()
