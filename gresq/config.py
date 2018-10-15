import os

try:
    import secrets
    secrets_found = True
except:
    secrets_found = False

class Config:
    secrets_found=secrets_found


class DevelopmentConfig(Config):

    def __init__(self):
        self.DEBUG = True
        self.DATABASEURI = os.environ.get('DEV_DATABASE_URL') or \
                  secrets.DEV_DATABASE_URL if self.secrets_found else \
                  'sqlite:////tmp/data-dev.sqlite'
        self.DATABASEARGS = os.environ.get('DEV_DATABASE_ARGS') or \
                  secrets.DEV_DATABASE_ARGS if self.secrets_found else \
                  None

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

config = {
        'development' : DevelopmentConfig(), \
        'test' : TestConfig()
        }
