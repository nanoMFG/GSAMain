from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


class Properties(Base):

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sample_id = Column(
        Integer,
        ForeignKey("sample.id", ondelete="CASCADE"),
        index=True,
        info={"verbose_name": "Sample ID"},
    )
    average_thickness_of_growth = Column(
        Float(precision=32),
        info={
            "verbose_name": "Average Thickness of Growth",
            "std_unit": "nm",
            "conversions": {"nm": 1},
            "required": False,
        },
    )
    standard_deviation_of_growth = Column(
        Float,
        info={
            "verbose_name": "St. Dev. of Growth",
            "std_unit": "nm",
            "conversions": {"nm": 1},
            "required": False,
        },
    )
    number_of_layers = Column(
        Integer,
        info={"verbose_name": "Number of Layers", "std_unit": None, "required": False},
    )
    growth_coverage = Column(
        Float,
        info={
            "verbose_name": "Growth Coverage",
            "std_unit": "%",
            "conversions": {"%": 1},
            "required": False,
        },
    )
    domain_size = Column(
        Float,
        info={
            "verbose_name": "Domain Size",
            "std_unit": "um^2",
            "conversions": {"um^2": 1},
            "required": False,
        },
    )
    shape = Column(
        String(32),
        info={
            "verbose_name": "Shape",
            "choices": ["Nondescript", "Hexagonal", "Square", "Circle"],
            "std_unit": None,
            "required": False,
        },
    )

    sample = relationship("Sample", uselist=False, back_populates="properties")

    def json_encodable(self):
        params = [
            "average_thickness_of_growth",
            "standard_deviation_of_growth",
            "number_of_layers",
            "growth_coverage",
            "domain_size",
            "shape",
        ]
        json_dict = {}
        for p in params:
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": getattr(Properties, p).info["std_unit"],
            }
        return json_dict
