from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Boolean,
    Float,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship

from grdb.database.v1_1_0 import Base


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
    software_name = Column(String(20), info={"verbose_name": "Analysis Software"})
    software_version = Column(String(20), info={"verbose_name": "Software Version"})
    __table_args__ = (
        ForeignKeyConstraint(
            [software_name, software_version],
            ["software.name", "software.version"],
            name="fk_sem_analysis_software",
        ),
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
        Boolean, info={"verbose_name": "Automated Detection"}, default=False
    )

    def json_encodable(self):
        return {
            "growth_coverage": {"value": self.growth_coverage, "unit": "%"},
            "px_per_um": {"value": self.px_per_um, "unit": "1/um"},
            "automated": {"value": self.automated, "unit": None},
        }
