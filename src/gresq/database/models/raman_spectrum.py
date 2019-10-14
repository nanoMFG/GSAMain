from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


class RamanSpectrum(Base):
    __tablename__ = "raman_spectrum"
    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    # set_id = Column(Integer,ForeignKey(raman_set.id), index=True, info={'verbose_name':'Raman Set ID'})
    raman_file_id = Column(
        Integer, ForeignKey("raman_file.id", ondelete="CASCADE"), index=True
    )
    xcoord = Column(Integer, info={"verbose_name": "X Coordinate"})
    ycoord = Column(Integer, info={"verbose_name": "Y Coordinate"})
    percent = Column(
        Float,
        info={
            "verbose_name": "Characteristic Percent",
            "std_unit": "%",
            "conversions": {"%": 1},
            "required": True,
        },
    )
    d_peak_shift = Column(
        Float,
        info={"verbose_name": "D Peak Shift", "std_unit": "cm^-1", "required": False},
    )
    d_peak_amplitude = Column(
        Float,
        info={"verbose_name": "D Peak Amplitude", "std_unit": None, "required": False},
    )
    d_fwhm = Column(
        Float, info={"verbose_name": "D FWHM", "std_unit": "cm^-1", "required": False}
    )
    g_peak_shift = Column(
        Float,
        info={"verbose_name": "G Peak Shift", "std_unit": "cm^-1", "required": False},
    )
    g_peak_amplitude = Column(
        Float,
        info={"verbose_name": "G Peak Amplitude", "std_unit": None, "required": False},
    )
    g_fwhm = Column(
        Float, info={"verbose_name": "G FWHM", "std_unit": "cm^-1", "required": False}
    )
    g_prime_peak_shift = Column(
        Float,
        info={"verbose_name": "G' Peak Shift", "std_unit": "cm^-1", "required": False},
    )
    g_prime_peak_amplitude = Column(
        Float,
        info={"verbose_name": "G' Peak Amplitude", "std_unit": None, "required": False},
    )
    g_prime_fwhm = Column(
        Float, info={"verbose_name": "G' FWHM", "std_unit": "cm^-1", "required": False}
    )

    raman_file = relationship(
        "RamanFile",
        uselist=False,
        back_populates="raman_spectrum",
        primaryjoin="RamanSpectrum.raman_file_id==RamanFile.id",
    )

    def json_encodable(self):
        params = [
            "percent",
            "d_peak_shift",
            "d_peak_amplitude",
            "d_fwhm",
            "g_peak_shift",
            "g_peak_amplitude",
            "g_fwhm",
            "g_prime_peak_shift",
            "g_prime_peak_amplitude",
            "g_prime_fwhm",
        ]
        json_dict = {}
        json_dict["raman_file"] = self.raman_file.json_encodable()
        for p in params:
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": getattr(RamanSpectrum, p).info["std_unit"],
            }

        return json_dict
