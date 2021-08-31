from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Date,
    Boolean,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class Software(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "software"

    name = Column(
        String(20),
        primary_key=True,
        info={"verbose_name": "Software Name", "required": True},
    )
    version = Column(
        String(20),
        primary_key=True,
        info={"verbose_name": "Software Version", "required": True},
    )
    release_date = Column(Date, info={"verbose_name": "Release Date", "required": True})
    branch = Column(String(32), info={"verbose_name": "Branch"})
    commitsh = Column(String(64), info={"verbose_name": "Commit SHA"})
    url = Column(String(128), info={"verbose_name": "URL"})

    def __repr__(self):
        return self._repr(
            name=self.name,
            version=self.version,
            release_date=self.release_date,
            branch=self.branch,
            commitsh=self.commitsh,
            url=self.url,
        )
