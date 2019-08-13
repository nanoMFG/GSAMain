import os

try:
    import secrets
    secrets_found = True
except:
    secrets_found = False

class Config:
    secrets_found=secrets_found

    def __init__(self, prefix , suffix = '', debug=False,multiarg=False):
        """Environment variables must use the prefix + _'URL' and prefix + '+ARGS'.
        To configure multiple Users, append env vars with '_user'.  For example,
            DEV_DATABASE_URL_USER1
            DEV_DATABASE_URL_USER2
        """
        self.DEBUG = debug
        self.PREFIX = prefix

        self.URL_var = prefix + '_URL' + suffix
        if multiarg:
            self.ARGS_var = prefix + '_ARGS' + suffix
        else:
            self.ARGS_var = prefix + '_ARGS'

        try:
            self.DATABASEURI = os.environ.get(self.URL_var) or \
            secrets.DEV_DATABASE_URL if self.secrets_found else \
            'sqlite://'
        except AttributeError:
            self.DATABASEURI =  'sqlite://'

        try:
            self.DATABASEARGS = os.environ.get(self.ARGS_var) or \
            secrets.DEV_DATABASE_ARGS if self.secrets_found else \
            None
        except AttributeError:
            self.DATABASEARGS = None




class MultiConfig(Config):

    def __init__(self, prefix, debug, instances):
        super().__init__(prefix=prefix, debug=debug)

        for i in instances:
            #print('"'+i['label']+'"',i['prefix'])
            if(i['label'] != ''):
                setattr(self, i['label'], Config(prefix=prefix, suffix=i['suffix'], debug=debug))
            #else():
            #    super().__init__(i['prefix'], debug)

def get_users(URL_var, ARGS_var):
    env = dict(os.environ)
    #print(env)
    urls = {}
    args = {}
    for key,val in env.items():
        if key.startswith(URL_var):
            urls[key] = val
        if key.startswith(ARGS_var):
            args[key] = val
    return urls, args

def config_factory(prefix, debug):
    URL_var = prefix + '_URL'
    ARGS_var = prefix + '_ARGS'
    urls, args = get_users(URL_var, ARGS_var)

    if len(urls) <= 1 and len(args) <= 1:
        return Config(prefix=prefix, debug=debug)

    if len(urls) > 1 and len(args) == 1:
        users = [ k[len(URL_var):] for k in urls]
        instances = []
        for u in users:
            clean_u = u[1:].lower()
            print(u, clean_u)
            instances.append({'label' : clean_u, 'suffix' : u})

        return MultiConfig(prefix, debug, instances)






class DevelopmentConfig(Config):
    """Simple configuration class for development environment.
    """

    def __init__(self,prefix='DEV_DATABASE', debug=True):
        super().__init__(prefix, debug)
#        self.DEBUG = True
#        try:
#            self.DATABASEURI = os.environ.get('DEV_DATABASE_URL') or \
#            secrets.DEV_DATABASE_URL if self.secrets_found else \
#            'sqlite://'
#        except AttributeError:
#            self.DATABASEURI =  'sqlite://'
#
#        try:
#            self.DATABASEARGS = os.environ.get('DEV_DATABASE_ARGS') or \
#            secrets.DEV_DATABASE_ARGS if self.secrets_found else \
#            None
#        except AttributeError:
#            self.DATABASEARGS = None


class TestConfig(Config):

    def __init__(self):
        self.DEBUG = True
        try:
            self.DATABASEURI = os.environ.get('TEST_DATABASE_URL') or \
            secrets.TEST_DATABASE_URL if self.secrets_found else \
            'sqlite://'
        except AttributeError:
            self.DATABASEURI =  'sqlite://'

        try:
            self.DATABASEARGS = os.environ.get('TEST_DATABASE_ARGS') or \
            secrets.TEST_DATABASE_ARGS if self.secrets_found else \
            None
        except AttributeError:
            self.DATABASEARGS = None

class ProductionConfig(Config):
    """Simple configuration class for production environment.
    """

    def __init__(self):
        self.DEBUG = False
        try:
            self.DATABASEURI = os.environ.get('PROD_DATABASE_URL') or \
            secrets.PROD_DATABASE_URL if self.secrets_found else \
            'sqlite://'
        except AttributeError:
            self.DATABASEURI =  'sqlite://'

        try:
            self.DATABASEARGS = os.environ.get('PROD_DATABASE_ARGS') or \
            secrets.PROD_DATABASE_ARGS if self.secrets_found else \
            None
        except AttributeError:
            self.DATABASEARGS = None

# Configuration dictionary to import
config = {
        'development' : config_factory('DEV_DATABASE',debug=True),
        'test' : TestConfig(),
        'production' : ProductionConfig()
        }
