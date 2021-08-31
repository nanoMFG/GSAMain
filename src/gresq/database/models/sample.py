from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Date,
    Boolean,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from grdb.database.v1_1_0 import Base


class Sample(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "sample"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement="ignore_fk",
        info={"verbose_name": "ID"},
    )
    software_name = Column(String(20), info={"verbose_name": "Analysis Software"})
    software_version = Column(String(20), info={"verbose_name": "Software Version"})

    primary_sem_file_id = Column(Integer, index=True)

    nanohub_userid = Column(Integer, info={"verbose_name": "Nanohub Submitter User ID"})
    experiment_date = Column(
        Date, info={"verbose_name": "Experiment Date", "required": True}
    )
    material_name = Column(
        String(32),
        info={
            "verbose_name": "Material Name",
            "choices": ["Graphene"],
            "required": True,
        },
    )
    validated = Column(Boolean, info={"verbose_name": "Validated"}, default=False)
    # ONE-TO_MANY: sample -> authors
    authors = relationship(
        "Author",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
        lazy="subquery",
    )
    # ONE-TO-ONE: sample -> recipe
    recipe = relationship(
        "Recipe",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
        lazy="subquery",
    )
    # ONE-TO-MANY: sample -> properties
    properties = relationship(
        "Properties",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
        lazy="subquery",
    )
    # ONE-TO-MANY: sample -> raman_files
    raman_files = relationship(
        "RamanFile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
        lazy="subquery",
    )

    raman_analysis = relationship(
        "RamanSet",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sample",
        lazy="subquery",
    )
    # ONE-TO-MANY: sample -> sem_files
    sem_files = relationship(
        "SemFile",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True,
        foreign_keys="SemFile.sample_id",
        back_populates="sample",
        lazy="subquery",
    )
    # Defining the foreign key constraint explictly (as below) prevents a sem_file id from
    # a different sample from being assigned to the primary_sem_file_id column.
    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "primary_sem_file_id"],
            ["sem_file.sample_id", "sem_file.id"],
            use_alter=True,
            ondelete="CASCADE",
            name="fk_primary_sem_file",
        ),
        ForeignKeyConstraint(
            [software_name, software_version],
            ["software.name", "software.version"],
            name="fk_gresq_software",
        ),
    )

    primary_sem_file = relationship(
        "SemFile",
        primaryjoin="Sample.primary_sem_file_id==SemFile.id",
        foreign_keys=primary_sem_file_id,
        uselist=False,
        post_update=True,
        lazy="subquery",
    )

    @hybrid_property
    def primary_sem_analysis(self):
        return self.primary_sem_file.default_analysis

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
