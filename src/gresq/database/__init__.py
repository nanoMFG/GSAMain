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
import typing
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import DetachedInstanceError

class_registry = {}


class Base(object):
    def __repr__(self) -> str:
        return self._repr(id=self.id)

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        """
        Helper for __repr__
        """
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f"{key}={field!r}")
            except DetachedInstanceError:
                field_strings.append(f"{key}=DetachedInstanceError")
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


# Base = declarative_base(cls=Base)
"""
sqlalchemy.ext.declarative.declarative_base:  The declarative_base class instance
to be used by all models and DataAccessLayer connections.
"""
Base = declarative_base(cls=Base, class_registry=class_registry)

from .dal import dal
