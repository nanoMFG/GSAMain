"""
Package init for gresq.database.  Currently all models are imported here to
provide implicit import support.

Examples:
    $ from gresq.database import sample

Todo:
    * Move to explicit imports eg:
    $ from gresq.database.model import sample_id
    * Possibly make model a Package.
"""
from sqlalchemy.ext.declarative import declarative_base
class_registry = {}
Base = declarative_base(class_registry=class_registry)
"""
sqlalchemy.ext.declarative.declarative_base:  The declarative_base class instance
to be used by all models and DataAccessLayer connections.
"""

from .dal import dal
