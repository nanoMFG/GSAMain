import pytest
from gresq.database.dal import dal
from gresq.database import Base
from gresq.config import Config

config_prefix = 'TEST_DATABASE'
config_suffix = '_ADMIN'

@pytest.fixture
def dal_conn():
    conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
    dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
    # Add some data here
    yield
    # Drop and ditch
    Base.metadata.drop_all(bind=dal.engine)
    dal.engine.dispose()

    

class TestDataAccessLayer:
    def test_init_db(self, dal_conn):
        """Test dal._init_db using the TEST_DATABASE_URL_ADMIN config. If this is
        not set ing the environment, the default engine will be sqlite.
        """
        
        