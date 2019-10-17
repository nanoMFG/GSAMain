import os

from gresq.config import Config
from gresq.database import dal
from gresq.util.csv2db3 import build_db
import logging

logging.basicConfig(level=logging.DEBUG)

config_prefix = "DEV_DATABASE"
config_suffix = "_ADMIN"

conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})

BOX_CONFIG_PATH = os.environ["BOX_CONFIG_PATH"]
csv2db_file = os.path.join(os.getcwd(), "data", "SEM_Raman_Data")

with dal.session_scope() as session:
    build_db(
        session,
        os.path.join(os.getcwd(), "data"),
        csv2db_file,
        box_config_path=BOX_CONFIG_PATH,
    )
