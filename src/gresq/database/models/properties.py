from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class Properties(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

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
            "tooltip": "Thickness of graphene present on the catalyst",
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
        Integer, info={"verbose_name": "Number of Layers", "required": False, "tooltip": "Number of layers of graphene present on the catalyst"}
    )
    growth_coverage = Column(
        Float,
        info={
            "verbose_name": "Growth Coverage",
            "std_unit": "%",
            "conversions": {"%": 1},
            "required": False,
            "tooltip": "Percentage of area covered by graphene, for a minimum area of 100 x 100 microns",
        },
    )
    domain_size = Column(
        Float,
        info={
            "verbose_name": "Domain Size",
            "std_unit": "um^2",
            "conversions": {"um^2": 1},
            "required": False,
            "tooltip": "Average size of graphene domains on the sample",
        },
    )
    shape = Column(
        String(32),
        info={
            "verbose_name": "Shape",
            "choices": ["Nondescript", "Hexagonal", "Square", "Circle"],
            "required": False,
            "tooltip": "Shape of the graphene domains",
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
            info = getattr(Properties, p).info
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": info["std_unit"] if "std_unit" in info else None,
            }
        return json_dict
