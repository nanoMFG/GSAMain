from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Boolean,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from gresq.database import Base


class SemAnalysis(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "sem_analysis"
    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sem_file_id = Column(
        Integer, ForeignKey("sem_file.id", ondelete="CASCADE"), index=True
    )
    __table_args__ = (UniqueConstraint("id", "sem_file_id"),)
    __mapper_args__ = {"confirm_deleted_rows": False}
    sem_file = relationship(
        "SemFile",
        back_populates="analyses",
        foreign_keys=[sem_file_id],
        lazy="subquery",
    )

    mask_url = Column(String(256))
    px_per_um = Column(Integer, info={"verbose_name": "Pixels/um"})
    growth_coverage = Column(
        Float,
        info={
            "verbose_name": "Growth Coverage",
            "std_unit": "%",
            "conversions": {"%": 1},
            "required": False,
        },
    )
    automated = Column(
        Boolean,
        info={"verbose_name": "Automated Detection"},
        default=False,
    )

    def json_encodable(self):
        return {
            "growth_coverage": {"value": self.growth_coverage, "unit": "%"},
            "px_per_um": {"value": self.px_per_um, "unit": "1/um"},
            "automated": {"value": self.automated, "unit": None},
        }
