import os
import pytest
from gresq.database.dal import dal
from gresq.database import Base
from gresq.config import Config
#from gresq.util.csv2db3 import build_db
from gresq.database.models import Sample

config_prefix = 'TEST_DATABASE'
config_suffix = '_ADMIN'
#csv2db_file = os.environ["CSV2DB_FILE"]
BOX_CONFIG_PATH = os.environ["BOX_CONFIG_PATH"]
csv2db_file = os.path.join(os.getcwd(),'data', 'SEM_Raman_Data')


@pytest.fixture
def dal_conn(scope="module"):
    conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
    dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
    # Add some data here
    yield
    # Drop and ditch
    Base.metadata.drop_all(bind=dal.engine)
    dal.engine.dispose()

def session(scope="function"):
    return dal.session_scope()

    

class TestDataAccessLayer:
    def test_init_db(self, dal_conn):
        """Test dal._init_db using the TEST_DATABASE_URL_ADMIN config. If this is
        not set ing the environment, the default engine will be sqlite.
        """
        pass


        
        