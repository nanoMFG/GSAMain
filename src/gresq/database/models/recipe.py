from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


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
            "conversions": {"um": 1},
            "required": False,
        },
    )
    diameter = Column(
        Float,
        info={
            "verbose_name": "Diameter",
            "std_unit": "um",
            "conversions": {"um": 1},
            "required": False,
        },
    )
    length = Column(
        Float,
        info={
            "verbose_name": "Length",
            "std_unit": "um",
            "conversions": {"um": 1},
            "required": False,
        },
    )

    # EXPERIMENTAL CONDITIONS:
    catalyst = Column(
        String(64),
        info={
            "verbose_name": "Catalyst",
            "choices": [],
            "std_unit": None,
            "required": True,
        },
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
            "conversions": {"Torr": 1, "Pa": 1 / 133.322, "mbar": 1 / 1.33322},
            "required": True,
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
    preparation_step = relationship(
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

    # @maximum_temperature.expression
    # def maximum_temperature(cls):
    #     return select([func.max(preparation_step.furnace_temperature)]).\
    #             where(preparation_step.recipe_id==cls.id).correlate(cls).\
    #             label('maximum_temperature')

    # @hybrid_property
    # def maximum_pressure(self):
    #     return max([p.furnace_pressure for p in self.preparation_steps if p.furnace_pressure!=None])

    # @maximum_pressure.expression
    # def maximum_pressure(cls):
    #     return select([func.max(preparation_step.furnace_pressure)]).\
    #             where(preparation_step.recipe_id==cls.id).correlate(cls).\
    #             label('maximum_pressure')

    # @hybrid_property
    # def average_carbon_flow_rate(self):
    #     steps = [p.carbon_source_flow_rate for p in self.preparation_steps if p.carbon_source_flow_rate!=None]
    #     return sum(steps)/len(steps)

    # @average_carbon_flow_rate.expression
    # def average_carbon_flow_rate(cls):
    #     return select([func.avg(preparation_step.carbon_source_flow_rate)]).\
    #             where(preparation_step.recipe_id==cls.id).correlate(cls).\
    #             label('average_carbon_flow_rate')

    # @hybrid_property
    # def carbon_source(self):
    #     vals = [p.carbon_source for p in self.preparation_steps if p.carbon_source is not None]
    #     return vals[0]

    # @carbon_source.expression
    # def carbon_source(cls):
    #     return select([preparation_step.carbon_source]).\
    #             where(and_(preparation_step.recipe_id==cls.id,preparation_step.carbon_source != None)).\
    #             correlate(cls).\
    #             limit(1).\
    #             label('carbon_source')

    # @hybrid_property
    # def uses_helium(self):
    #     return any([p.helium_flow_rate for p in self.preparation_steps])

    # @uses_helium.expression
    # def uses_helium(cls):
    #     s = select([preparation_step.helium_flow_rate]).\
    #             where(and_(preparation_step.helium_flow_rate != None,preparation_step.recipe_id==cls.id)).\
    #             correlate(cls)
    #     return exists(s)

    # @hybrid_property
    # def uses_argon(self):
    #     return any([p.argon_flow_rate for p in self.preparation_steps])

    # @uses_argon.expression
    # def uses_argon(cls):
    #     s = select([preparation_step.argon_flow_rate]).\
    #             where(and_(preparation_step.argon_flow_rate != None,preparation_step.recipe_id==cls.id)).\
    #             correlate(cls)
    #     return exists(s)

    # @hybrid_property
    # def uses_hydrogen(self):
    #     return any([p.hydrogen_flow_rate for p in self.preparation_steps])

    # @uses_hydrogen.expression
    # def uses_hydrogen(cls):
    #     s = select([preparation_step.hydrogen_flow_rate]).\
    #             where(and_(preparation_step.hydrogen_flow_rate != None,preparation_step.recipe_id==cls.id)).\
    #             correlate(cls)
    #     return exists(s)

    # def json_encodable(self):
    #     params = [
    #         "catalyst",
    #         "tube_diameter",
    #         "cross_sectional_area",
    #         "tube_length",
    #         "base_pressure",
    #         "thickness",
    #         "diameter",
    #         "length",
    #         "dewpoint"
    #         ]
    #     json_dict = {}
    #     for p in params:
    #         json_dict[p] = {'value':getattr(self,p),'unit':getattr(recipe,p).info['std_unit']}
    #     json_dict['preparation_steps'] = sorted([s.json_encodable() for s in self.preparation_steps if s.step!=None] , key= lambda s: s["step"])

    #     return json_dict