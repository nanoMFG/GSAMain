from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class MdfForge(Base):
    __tablename__ = "mdf_forge"
    mdf_id = Column(String(32), primary_key=True, info={"verbose_name": "MDF ID"})
    title = Column(String(64), info={"verbose_name": "Title"})
    catalyst = Column(String(32), info={"verbose_name": "Catalyst"})
    max_temperature = Column(Float, info={"verbose_name": "Maximum Temperature"})
    carbon_source = Column(String(32), info={"verbose_name": "Carbon Source"})
    base_pressure = Column(Float, info={"verbose_name": "Base Pressure"})

    sample_surface_area = Column(Float, info={"verbose_name": "Sample Surface Area"})
    sample_thickness = Column(Float, info={"verbose_name": "Sample Thickness"})

    orientation = Column(Float, info={"verbose_name": "Orientation"})
    grain_size = Column(Float, info={"verbose_name": "Grain Size"})
