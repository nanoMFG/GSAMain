import os

from gresq.config import Config
from grdb.database.v1_1_0 import dal, Base
from grdb.database.v1_1_0.models import Sample
import logging
logging.basicConfig(level=logging.DEBUG)

config_prefix = "DEV_DATABASE"
config_suffix = "_ADMIN"

conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})

with dal.session_scope(autocommit=True) as sess:
    for s in sess.query(Sample).all():
        sess.delete(s)
dal.Session().close()
#print(Base.metadata.tables)
ret = Base.metadata.drop_all(bind=dal.engine)
print(f"ret: {ret}")

