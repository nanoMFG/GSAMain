from sqlalchemy import Column, String, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class PreparationStep(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "preparation_step"

    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})

    recipe_id = Column(
        Integer,
        ForeignKey("recipe.id", ondelete="CASCADE"),
        info={"verbose_name": "Recipe ID"},
        index=True,
    )
    # MANY-TO-ONE: preparation_step->recipe
    recipe = relationship("Recipe", uselist=False, back_populates="preparation_steps")

    step = Column(Integer)
    name = Column(
        String(16),
        info={
            "verbose_name": "Name",
            "choices": ["Annealing", "Growing", "Cooling"],
            "required": True,
        },
    )
    duration = Column(
        Float,
        info={
            "verbose_name": "Duration",
            "std_unit": "min",
            "conversions": {"min": 1, "sec": 1 / 60.0, "hrs": 60},
            "required": True,
        },
    )
    furnace_temperature = Column(
        Float,
        info={
            "verbose_name": "Furnace Temperature",
            "std_unit": "C",
            "conversions": {"C": 1},
            "required": True,
        },
    )
    furnace_pressure = Column(
        Float,
        info={
            "verbose_name": "Furnace Pressure",
            "std_unit": "Torr",
            "conversions": {"Torr": 1, "Pa": 1 / 133.322, "mbar": 1 / 1.33322, "mTorr":1.0e-3},
            "required": True,
        },
    )
    sample_location = Column(
        Float,
        info={
            "verbose_name": "Sample Location",
            "std_unit": "mm",
            "conversions": {"inches": 25.4, "mm": 1},
            "required": False,
            "tooltip": "Position of the sample in the tube",
        },
    )
    helium_flow_rate = Column(
        Float,
        info={
            "verbose_name": "Helium Flow Rate",
            "std_unit": "sccm",
            "conversions": {"sccm": 1},
            "required": False,
        },
    )
    hydrogen_flow_rate = Column(
        Float,
        info={
            "verbose_name": "Hydrogen Flow Rate",
            "std_unit": "sccm",
            "conversions": {"sccm": 1},
            "required": False,
        },
    )
    carbon_source = Column(
        String(16),
        info={
            "verbose_name": "Carbon Source",
            "choices": ["CH4", "C2H4", "C2H2", "C6H6"],
            "required": True,
        },
    )
    carbon_source_flow_rate = Column(
        Float,
        info={
            "verbose_name": "Carbon Source Flow Rate",
            "std_unit": "sccm",
            "conversions": {"sccm": 1},
            "required": True,
        },
    )
    argon_flow_rate = Column(
        Float,
        info={
            "verbose_name": "Argon Flow Rate",
            "std_unit": "sccm",
            "conversions": {"sccm": 1},
            "required": False,
        },
    )
    cooling_rate = Column(
        Float,
        info={
            "verbose_name": "Cooling Rate",
            "std_unit": "C/min",
            "conversions": {"C/min": 1},
            "required": False,
        },
    )

    def json_encodable(self):
        params = [
            "name",
            "duration",
            "furnace_temperature",
            "furnace_pressure",
            "sample_location",
            "helium_flow_rate",
            "hydrogen_flow_rate",
            "carbon_source",
            "carbon_source_flow_rate",
            "argon_flow_rate",
        ]

        if self.name == "Cooling":
            params.append("cooling_rate")

        json_dict = {}
        json_dict["step"] = self.step
        for p in params:
            info = getattr(PreparationStep, p).info
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": info["std_unit"] if "std_unit" in info else None,
            }

        return json_dict
