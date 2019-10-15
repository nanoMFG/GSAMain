from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


class Sample(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "sample"

    id = Column(
        Integer, primary_key=True, info={"verbose_name": "ID", "std_unit": None}
    )
    nanohub_userid = Column(
        Integer, info={"verbose_name": "Nanohub Submitter User ID", "std_unit": None}
    )
    experiment_date = Column(
        Date,
        info={"verbose_name": "Experiment Date", "required": True, "std_unit": None},
    )
    material_name = Column(
        String(32),
        info={
            "verbose_name": "Material Name",
            "choices": ["Graphene"],
            "required": True,
            "std_unit": None,
        },
    )
    validated = Column(
        Boolean, info={"verbose_name": "Validated", "std_unit": None}, default=False
    )
    # ONE-TO_MANY: sample -> author
    authors = relationship(
        "Author",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
    )

    recipe = relationship(
        "Recipe",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
    )

    properties = relationship(
        "Properties",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
    )

    raman_files = relationship(
        "RamanFile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
    )

    # raman_analysis = relationship("raman_set", uselist=False)

    sem_files = relationship(
        "SemFile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
    )
    # primary_sem_file_id = Column(Integer,ForeignKey("sem_analysis.id",use_alter=True),index=True)
    # primary_sem_file = relationship(
    #     "sem_file", primaryjoin="sample.primary_sem_file_id==sem_file.id",
    #     foreign_keys = [primary_sem_file_id],
    #     uselist=False, post_update=True)

    # @hybrid_property
    # def primary_sem_analysis(self):
    #     return self.primary_sem_file.default_analysis

    # @hybrid_property
    # def sem_analyses(self):
    #     return [s.default_analysis for s in self.sem_files]

    @hybrid_property
    def author_last_names(self):
        return ", ".join(sorted([a.last_name for a in self.authors if a.last_name]))

    # @author_last_names.expression
    # def author_last_names(cls): # BROKEN
    #     selection = select([func.group_concat(author.last_name)]).\
    #             where(author.sample_id==cls.id).\
    #             correlate(cls)

    def json_encodable(self):
        return {
            "primary_key": self.id,
            "material_name": self.material_name,
            "experiment_date": self.experiment_date.timetuple(),
            "authors": [s.json_encodable() for s in self.authors],
            "recipe": self.recipe.json_encodable(),
            "properties": self.properties.json_encodable(),
        }
