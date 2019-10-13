from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


class RamanFile(Base):
    __tablename__ = "raman_file"
    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    sample_id = Column(Integer, ForeignKey("sample.id", ondelete="CASCADE"), index=True)
    filename = Column(String(64))
    url = Column(String(256))
    wavelength = Column(
        Float,
        info={
            "verbose_name": "Wavelength",
            "std_unit": "nm",
            "conversions": {"nm": 1},
            "required": True,
        },
    )

    sample = relationship("Sample", back_populates="raman_files")

    raman_spectrum = relationship("RamanSpectrum", uselist=False, cascade="all, delete-orphan",
        passive_deletes=True, back_populates="raman_file")

    def json_encodable(self):
        params = ["wavelength"]
        json_dict = {}
        json_dict["filename"] = self.filename
        for p in params:
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": getattr(RamanFile, p).info["std_unit"],
            }
        return json_dict
