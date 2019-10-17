import os
import pytest
from gresq.database.dal import dal
from gresq.database import Base
from gresq.config import Config
from gresq.util.csv2db3 import build_db

BOX_CONFIG_PATH = os.environ["BOX_CONFIG_PATH"]
csv2db_file = os.path.join(os.getcwd(),'data', 'SEM_Raman_Data')
from ..database import config_prefix, config_suffix

@pytest.fixture(scope="module")
def csv2db():
    conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
    dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
    # Add some data here
    with dal.session_scope() as session:
        build_db(session, os.path.join(os.getcwd(),'data'), csv2db_file, nrun=31, box_config_path=BOX_CONFIG_PATH)
    yield
    # Drop and ditch
    Base.metadata.drop_all(bind=dal.engine)

class TestCsv2DB:
    def test_query_samples(self, csv2db):
        pass