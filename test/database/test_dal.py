import os
import pytest
from gresq.database.dal import dal
from gresq.database import Base
from gresq.config import Config
#from gresq.util.csv2db3 import build_db
from gresq.database.models import Sample
from faker import Faker

fake = Faker()
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
    #Base.metadata.drop_all(bind=dal.engine)
    dal.engine.dispose()

def session(scope="funcion"):
    return dal.session_scope()

# @pytest.fixture
# def testdb(scope="module"):
#     conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
#     dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
#     # Add some data here
#     with dal.session_scope() as session:
#         build_db(session, os.path.join(os.getcwd(),'data'), csv2db_file, nrun=3, box_config_path=BOX_CONFIG_PATH)
#     yield
#     # Drop and ditch
#     Base.metadata.drop_all(bind=dal.engine)
#     dal.engine.dispose()
    

class TestDataAccessLayer:
    def test_init_db(self, dal_conn):
        """Test dal._init_db using the TEST_DATABASE_URL_ADMIN config. If this is
        not set ing the environment, the default engine will be sqlite.
        """
        pass

class TestSample:
    def test_create(self, dal_conn, session):
        pass


    # def test_csv2db3_build_db(self, testdb):
    #     return 1
    #     #with dal.session_scope() as session:
    #     #    build_db(session, os.path.join(os.getcwd(),'data'), csv2db_file, nrun=34, box_config_path=BOX_CONFIG_PATH)
    #     #    #Base.metadata.drop_all(bind=dal.engine)
    
    # def test_some_query(self, testdb):
    #     with dal.session_scope() as session:
    #         for row in session.query(sample):
    #             print(row.id)

        
        