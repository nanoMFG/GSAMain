from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class Author(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "author"

    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sample_id = Column(
        Integer,
        ForeignKey("sample.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        info={"verbose_name": "Sample ID"},
    )
    raman_id = Column(
        Integer,
        ForeignKey("raman_set.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        info={"verbose_name": "Raman Set ID"},
    )
    first_name = Column(
        String(64), info={"verbose_name": "First Name", "required": False}
    )
    last_name = Column(
        String(64), info={"verbose_name": "Last Name", "required": False}
    )
    institution = Column(
        String(64), info={"verbose_name": "Institution", "required": False}
    )

    sample = relationship("Sample", back_populates="authors")

    raman_set = relationship("RamanSet", foreign_keys=[raman_id])

    @hybrid_property
    def full_name_and_institution(self):
        return "%s, %s   (%s)" % (self.last_name, self.first_name, self.institution)

    def json_encodable(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "institution": self.institution,
        }
