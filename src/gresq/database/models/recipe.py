from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func, text, and_
from sqlalchemy.sql import exists

from grdb.database.v1_1_0 import Base, class_registry


class Recipe(Base):
    __tablename__ = "recipe"

    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sample_id = Column(
        Integer,
        ForeignKey("sample.id", ondelete="CASCADE"),
        index=True,
        info={"verbose_name": "Sample ID"},
    )
    # SUBSTRATE
    thickness = Column(
        Float,
        info={
            "verbose_name": "Thickness",
            "std_unit": "um",
            "conversions": {"um": 1,"mm":1.0e-3},
            "required": False,
            "tooltip": "Sample thickness",
        },
    )
    diameter = Column(
        Float,
        info={
            "verbose_name": "Diameter",
            "std_unit": "um",
            "conversions": {"um": 1,"mm":1.0e-3},
            "required": False,
            "tooltip": "Sample diameter",
        },
    )
    length = Column(
        Float,
        info={
            "verbose_name": "Length",
            "std_unit": "um",
            "conversions": {"um": 1,"mm":1.0e-3},
            "required": False,
            "tooltip": "Sample length",
        },
    )

    # EXPERIMENTAL CONDITIONS:
    catalyst = Column(
        String(64), info={"verbose_name": "Catalyst", "choices": [], "required": True,"tooltip":"Select one from the list or add your own"}
    )
    tube_diameter = Column(
        Float(precision=32),
        info={
            "verbose_name": "Tube Diameter",
            "std_unit": "mm",
            "conversions": {"mm": 1, "inches": 25.4},
            "required": False,
        },
    )
    cross_sectional_area = Column(
        Float,
        info={
            "verbose_name": "Cross Sectional Area",
            "std_unit": "mm^2",
            "conversions": {"mm^2": 1, "inches^2": 25.4 ** 2},
            "required": False,
            "tooltip": "Cross sectional area of the tube",
        },
    )
    tube_length = Column(
        Float,
        info={
            "verbose_name": "Tube Length",
            "std_unit": "mm",
            "conversions": {"mm": 1, "inches": 25.4},
            "required": False,
        },
    )
    base_pressure = Column(
        Float,
        info={
            "verbose_name": "Base Pressure",
            "std_unit": "Torr",
            "conversions": {"Torr": 1, "Pa": 1 / 133.322, "mbar": 1 / 1.33322, 'mTorr': 1.0e-3},
            "required": True,
            "tooltip": "Pressure inside the tube before starting the flow of gases",
        },
    )
    dewpoint = Column(
        Float,
        info={
            "verbose_name": "Dew Point",
            "std_unit": "C",
            "conversions": {"C": 1},
            "required": False,
        },
    )
    sample_surface_area = Column(
        Float,
        info={
            "verbose_name": "Sample Surface Area",
            "std_unit": "mm^2",
            "conversions": {"mm^2": 1},
            "required": False,
        },
    )

    # ONE-TO-MANY: recipe -> preparation_step
    preparation_steps = relationship(
        "PreparationStep",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="recipe",
    )

    # ONE-TO-ONE: recipe -> sample
    sample = relationship("Sample", uselist=False, back_populates="recipe")

    @hybrid_property
    def maximum_temperature(self):
        return max(
            [
                p.furnace_temperature
                for p in self.preparation_steps
                if p.furnace_temperature != None
            ]
        )

    @maximum_temperature.expression
    def maximum_temperature(cls):
        PreparationStep = class_registry["PreparationStep"]
        return (
            select([func.max(PreparationStep.furnace_temperature)])
            .where(PreparationStep.recipe_id == cls.id)
            .correlate(cls)
            .label("maximum_temperature")
        )

    @hybrid_property
    def maximum_pressure(self):
        return max(
            [
                p.furnace_pressure
                for p in self.preparation_steps
                if p.furnace_pressure != None
            ]
        )

    @maximum_pressure.expression
    def maximum_pressure(cls):
        PreparationStep = class_registry["PreparationStep"]
        return (
            select([func.max(PreparationStep.furnace_pressure)])
            .where(PreparationStep.recipe_id == cls.id)
            .correlate(cls)
            .label("maximum_pressure")
        )

    @hybrid_property
    def average_carbon_flow_rate(self):
        steps = [
            p.carbon_source_flow_rate
            for p in self.preparation_steps
            if p.carbon_source_flow_rate != None
        ]
        return sum(steps) / len(steps)

    @average_carbon_flow_rate.expression
    def average_carbon_flow_rate(cls):
        PreparationStep = class_registry["PreparationStep"]
        return (
            select([func.avg(PreparationStep.carbon_source_flow_rate)])
            .where(PreparationStep.recipe_id == cls.id)
            .correlate(cls)
            .label("average_carbon_flow_rate")
        )

    # NOTE: This is really the carbon source from the first step.
    # Should there be a contraint that the carbon source is the same for all steps??
    @hybrid_property
    def carbon_source(self):
        vals = [
            p.carbon_source
            for p in self.preparation_steps
            if p.carbon_source is not None
        ]
        return vals[0]

    @carbon_source.expression
    def carbon_source(cls):
        PreparationStep = class_registry["PreparationStep"]
        return (
            select([PreparationStep.carbon_source])
            .where(
                and_(
                    PreparationStep.recipe_id == cls.id,
                    PreparationStep.carbon_source != None,
                )
            )
            .correlate(cls)
            .limit(1)
            .label("carbon_source")
        )

    @hybrid_property
    def uses_helium(self):
        return any([p.helium_flow_rate for p in self.preparation_steps])

    @uses_helium.expression
    def uses_helium(cls):
        PreparationStep = class_registry["PreparationStep"]
        s = (
            select([PreparationStep.helium_flow_rate])
            .where(
                and_(
                    PreparationStep.helium_flow_rate != None,
                    PreparationStep.recipe_id == cls.id,
                )
            )
            .correlate(cls)
        )
        return exists(s)

    @hybrid_property
    def uses_argon(self):
        return any([p.argon_flow_rate for p in self.preparation_steps])

    @uses_argon.expression
    def uses_argon(cls):
        PreparationStep = class_registry["PreparationStep"]
        s = (
            select([PreparationStep.argon_flow_rate])
            .where(
                and_(
                    PreparationStep.argon_flow_rate != None,
                    PreparationStep.recipe_id == cls.id,
                )
            )
            .correlate(cls)
        )
        return exists(s)

    @hybrid_property
    def uses_hydrogen(self):
        return any([p.hydrogen_flow_rate for p in self.preparation_steps])

    @uses_hydrogen.expression
    def uses_hydrogen(cls):
        PreparationStep = class_registry["PreparationStep"]
        s = (
            select([PreparationStep.hydrogen_flow_rate])
            .where(
                and_(
                    PreparationStep.hydrogen_flow_rate != None,
                    PreparationStep.recipe_id == cls.id,
                )
            )
            .correlate(cls)
        )
        return exists(s)

    def json_encodable(self):
        params = [
            "catalyst",
            "tube_diameter",
            "cross_sectional_area",
            "tube_length",
            "base_pressure",
            "thickness",
            "diameter",
            "length",
            "dewpoint",
        ]
        json_dict = {}
        for p in params:
            info = getattr(Recipe, p).info
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": info["std_unit"] if "std_unit" in info else None,
            }
        json_dict["preparation_steps"] = sorted(
            [s.json_encodable() for s in self.preparation_steps if s.step != None],
            key=lambda s: s["step"],
        )

        return json_dict
