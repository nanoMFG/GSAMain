from sqlalchemy import Column, String, Integer, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship

from gresq.database import Base


class SemFile(Base):
    __tablename__ = "sem_file"
    id = Column(Integer, primary_key=True, autoincrement='ignore_fk', info={"verbose_name": "ID"})
    sample_id = Column(Integer, ForeignKey("sample.id", ondelete="CASCADE"), index=True)
    filename = Column(String(64))
    url = Column(String(256))

    sample = relationship("Sample", back_populates="sem_files")

    default_analysis_id = Column(
        Integer,
        index=True,
    )
    # ForeignKey("sem_analysis.id", name="fk_default_analysis_id"),
    # ForeignKeyConstraint(
    #     ["default_analysis_id"], ["sem_analysis.id"],
    #     name='fk_sem_default_analysis_id', use_alter=True
    # )

    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "default_analysis_id"],
            ["sem_analysis.sem_file_id", "sem_analysis.id"],
            use_alter=True, ondelete="CASCADE",
            name="fk_default_analysis"
        ),
    )
    __mapper_args__ = {
        "confirm_deleted_rows": False
    }

    analyses = relationship(
        "SemAnalysis", cascade="all, delete-orphan",
        primaryjoin = "SemFile.id==SemAnalysis.sem_file_id",
        passive_deletes=True,
        single_parent=True,
        foreign_keys="SemAnalysis.sem_file_id",
        back_populates="sem_file",
        lazy='subquery'
        )

    default_analysis = relationship(
        "SemAnalysis",
        primaryjoin = "SemFile.default_analysis_id==SemAnalysis.id",
        foreign_keys=default_analysis_id,
        post_update=True,
        lazy='subquery'
        )


    def json_encodable(self):
        return {"filename": self.filename}
