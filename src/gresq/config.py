import os, importlib
import logging

logger = logging.getLogger(__name__)

# try:
#    #from . import gresq_app_secrets as secrets
#    spec = importlib.util.spec_from_file_location('gresq.gresq_app_secrets', '/Users/dadams/gresq_app_secrets.py')
#    secrets = importlib.util.module_from_spec(spec)
#    spec.loader.exec_module(secrets)
#
#    secrets_found = True
#    print(dir(secrets))
#    print(secrets.__file__)
#    print(secrets.__name__)
#    print(secrets.__package__)
# except:
#    secrets_found = False


class Config:
    """Configuration class.  Primariy designed for configuring database connections.
    Instances of this class can be passed to init_db in database.py
    Done:
        - Per user database urls

    To do:
        - Allow per user database arguments (_ARGS).
        - Define and throw exceptions when needed.
    """

    # secrets_found=secrets_found

    def __init__(
        self,
        prefix,
        suffix="",
        debug=False,
        multiarg=False,
        dbconfig_file="",
        try_secrets=True,
    ):
        """Recognized environment variables are of the form:
               prefix + '_URL' + ['_suffix']   and
               prefix + '_ARGS'
        The suffix label is optional for configuration of multiple user connections.
        To configure multiple Users, append the URL env vars with a '_user' label as the
        suffix.
        For example,
            DEV_DATABASE_URL_USER1
            DEV_DATABASE_URL_USER2
        A single set of _ARGS can be used for multiple URLs.
        Currently suffixes are not supported for ARGS variables.
        """
        # secrets = importlib.import_module('gresq.gresq_app_secrets','gresq')
        # secrets_found = True
        # print(dir(secrets))
        # print(secrets.__file__)
        # print(secrets.__name__)
        # print(secrets.__package__)
        self.secrets_found = False
        if try_secrets:
            if os.path.isfile(dbconfig_file):
                try:
                    spec = importlib.util.spec_from_file_location(
                        "gresq.gresq_app_secrets", dbconfig_file
                    )
                    secrets = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(secrets)
                    self.secrets_found = True
                except:
                    self.secrets_found = False
            else:
                try:
                    from . import gresq_app_secrets as secrets

                    self.secrets_found = True
                except:
                    self.secrets_found = False

        logger.debug("secrets_found:")
        logger.debug(self.secrets_found)
        self.DEBUG = debug
        self.PREFIX = prefix

        self.URL_var = prefix + "_URL" + suffix
        if multiarg:
            self.ARGS_var = prefix + "_ARGS" + suffix
        else:
            self.ARGS_var = prefix + "_ARGS"

        logger.debug(self.URL_var)
        try:
            self.DATABASEURI = (
                os.environ.get(self.URL_var) or getattr(secrets, self.URL_var)
                if self.secrets_found
                else "sqlite://"
            )
        except AttributeError:
            self.DATABASEURI = "sqlite://"

        try:
            self.DATABASEARGS = (
                os.environ.get(self.ARGS_var) or getattr(secrets, self.ARGS_var)
                if self.secrets_found
                else None
            )
        except AttributeError:
            self.DATABASEARGS = None

        if os.environ.get(self.URL_var):
            try:
                self.DATABASEURI = os.environ.get(self.URL_var)
            except AttributeError:
                self.DATABASEURI = "sqlite://"

            try:
                self.DATABASEARGS = os.environ.get(self.ARGS_var)
            except AttributeError:
                self.DATABASEARGS = None


class MultiConfig(Config):
    """Generate multiple Config class instances."""

    def __init__(self, prefix, debug, instances):
        super().__init__(prefix=prefix, debug=debug)

        for i in instances:
            # print('"'+i['label']+'"',i['prefix'])
            if i["label"] != "":
                setattr(
                    self,
                    i["label"],
                    Config(prefix=prefix, suffix=i["suffix"], debug=debug),
                )
            # else():
            # Should throw exception here...
            #    super().__init__(i['prefix'], debug)


def get_users(URL_var, ARGS_var):
    """Parse the environment searching for URL_var and ARGS_var.
    Return a dictionary of matching vars and their values.
    """
    env = dict(os.environ)
    # print(env)
    urls = {}
    args = {}
    # print('hey')
    # print(os.environ.get(URL_var))
    for key, val in env.items():
        if key.startswith(URL_var):
            urls[key] = val
        if key.startswith(ARGS_var):
            args[key] = val
    # print(urls)
    return urls, args


def config_factory(prefix, debug):
    """For a given prefix and debug setting, generate a Config or MultiConfig class
    and return it.
    """
    URL_var = prefix + "_URL"
    ARGS_var = prefix + "_ARGS"
    urls, args = get_users(URL_var, ARGS_var)

    # Possible secrets file, only for 1 DB config for now

    if len(urls) == 0:
        return Config(prefix=prefix, debug=debug)

    if len(urls) <= 1 and len(args) <= 1:
        return Config(prefix=prefix, debug=debug)

    elif len(urls) > 1 and len(args) == 1:
        users = [k[len(URL_var) :] for k in urls]
        instances = []
        for u in users:
            clean_u = u[1:].lower()
            # print(u, clean_u)
            instances.append({"label": clean_u, "suffix": u})
        return MultiConfig(prefix, debug, instances)

    # elif len(urls) > 1 and len(args) > 1 and len(urls) == len(args):

    # else
    # throw exception


# Configuration dictionary with pre-defined prefixes to import into apps.
config = {
    "development": config_factory(prefix="DEV_DATABASE", debug=True),
    "test": config_factory(prefix="TEST_DATABASE", debug=True),
    "production": config_factory(prefix="PROD_DATABASE", debug=False),
}
