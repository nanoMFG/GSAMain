from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from gresq.database import Base


class SemFile(Base):
    __tablename__ = "sem_file"
    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sample_id = Column(Integer, ForeignKey("sample.id", ondelete="CASCADE"), index=True)
    filename = Column(String(64))
    url = Column(String(256))

    sample = relationship("Sample", back_populates="sem_files")

    # default_analysis_id = Column(
    #     Integer, ForeignKey("sem_analysis.id", use_alter=True),
    #     index=True
    #     )

    # default_analysis = relationship(
    #     "sem_analysis",
    #     primaryjoin = "sem_file.default_analysis_id==sem_analysis.id",
    #     foreign_keys = [default_analysis_id],
    #     post_update=True,
    #     lazy='subquery'
    #     )

    analyses = relationship(
        "SemAnalysis", cascade="all, delete-orphan",
        passive_deletes=True,
        back_populates="sem_file",
        lazy='subquery'
        )

    def json_encodable(self):
        return {"filename": self.filename}
