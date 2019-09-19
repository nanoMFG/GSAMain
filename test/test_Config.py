import os
import importlib
import pytest
import gresq.config

#from gresq.testing import fixtures

vars_dict = {'DEV_DATABASE_URL' : '', 'DEV_DATABASE_ARGS' : '',
             'DEV_DATABASE_URL_READ' : '', 'DEV_DATABASE_ARGS_READ' : '',
             'DEV_DATABASE_URL_WRITE' : '', 'DEV_DATABASE_ARGS_WRITE' : '',
             'DEV_DATABASE_URL_ADMIN' : '', 'DEV_DATABASE_ARGS_ADMIN' : '',
             'TEST_DATABASE_URL' : '', 'TEST_DATABASE_ARGS' : '',
             'TEST_DATABASE_URL_READ' : '', 'TEST_DATABASE_ARGS_READ' : '',
             'TEST_DATABASE_URL_WRITE' : '', 'TEST_DATABASE_ARGS_WRITE' : ''
             }

config_prefix = 'TEST_DATABASE'
tmpdir = '/tmp'
tmp_secrets_file = tmpdir + '/gresq_app_secrets.py'

class ConfigTester:
    def __init__(prefix):
        url_key = prefix + '_URL'
        url_val = url_key + ':check_url'
        args_key = prefix + '_ARGS'
        args_val = args_key + ':check_args'


@pytest.fixture
def set_single_env_vars():
    pass

@pytest.fixture
def set_multi_env_vars():
    pass

@pytest.fixture
def unset_env_vars():
    """unset environment and secrets file to test defaults
    """
    #print("unsetting env")
    for k in vars_dict.keys():
        val = os.getenv(k)
        if val:
            #print(f"unsetting {k} = {os.environ[k]}")
            vars_dict[k] = val
            #os.unsetenv(k)
            del os.environ[k]

    yield

    # Teardown, put things back the way they were...
    #print ("resetting env")
    for k, v in vars_dict.items():
        if v != '':
            #print (f"setting: {k} = {v}")
            #os.putenv(k, v)
            #setattr(os.environ,k,v)
            os.environ[k]=v
            #print(os.environ[k])
        vars_dict[k] = ''

@pytest.fixture
def make_file_secrets(request):
    #print("setting file secrets")
    tmpfile = getattr(request.module, "tmp_secrets_file", "/tmp/testsecrets.py")
    prefix = getattr(request.module, "config_prefix", "TEST_DATABASE")
    db_url = prefix + '_URL'
    db_args = prefix + '_ARGS'
    with open(tmpfile, 'w') as f:
        f.write(db_url + " = 'check_secrets_url'\n")
        f.write(db_args + "= 'check_secrets_args'\n")

    yield

    os.remove(tmpfile)

@pytest.fixture
def make_env_secrets(request):
    #print("setting env secrets")
    check_url = 'check_env_secrets_url'
    check_args ='check_env_secrets_args'
    prefix = getattr(request.module, "config_prefix", "TEST_DATABASE")
    url_k = prefix + '_URL'
    url_v = prefix + check_url
    args_k = prefix + '_ARGS'
    args_v = prefix + check_args
    os.environ.putenv(url_k, url_v)
    os.environ.putenv(args_k, args_v)
    os.environ[url_k] = url_v
    os.environ[args_k]= args_v



class TestConfig:
    def test_Defaults(self, unset_env_vars):
        conf = gresq.config.Config(prefix=config_prefix, debug=True, try_secrets=False)
        assert(conf.DATABASEURI == 'sqlite://')
        assert(conf.DATABASEARGS == None)

    def test_Secrets(self, unset_env_vars, make_file_secrets):
        conf = gresq.config.Config(prefix=config_prefix, debug=True, dbconfig_file=tmp_secrets_file, try_secrets=True)
        assert conf.DATABASEURI == 'check_secrets_url'
        assert conf.DATABASEARGS == 'check_secrets_args'

    def test_env(self, unset_env_vars, make_env_secrets):
        conf = gresq.config.Config(prefix=config_prefix, debug=True, try_secrets=False)
        assert conf.DATABASEURI == config_prefix+'check_env_secrets_url'
        assert conf.DATABASEARGS == config_prefix+'check_env_secrets_args'

    def test_env_takes_precident(self ,unset_env_vars, make_file_secrets, make_env_secrets):
        conf = gresq.config.Config(prefix=config_prefix, debug=True, dbconfig_file=tmp_secrets_file, try_secrets=True)
        assert conf.DATABASEURI == config_prefix+'check_env_secrets_url'
        assert conf.DATABASEARGS == config_prefix+'check_env_secrets_args'
