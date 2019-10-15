import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from gresq.database import Base


class RamanSet(Base):
    """[summary]
    
    Args:
        Base ([type]): [description]
    
    Returns:
        [type]: [description]
    """

    __tablename__ = "raman_set"
    id = Column(Integer, primary_key=True, info={"verbose_name": "ID"})
    nanohub_userid = Column(Integer, info={"verbose_name": "Nanohub Submitter User ID"})
    map_file = Column(Boolean, info={"verbose_name": "Map File"}, default=False)
    sample_id = Column(
        Integer,
        ForeignKey("sample.id", ondelete="CASCADE"),
        index=True,
        info={"verbose_name": "Sample ID"},
    )
    # raman_spectra = relationship("RamanSpectrum", back_populates="raman_set")

    authors = relationship(
        "Author",
        cascade="all, delete-orphan",
        passive_deletes=True,
        primaryjoin="raman_set.id==author.raman_id",
        back_populates="raman_set",
    )

    experiment_date = Column(
        Date,
        default=datetime.date.today,
        info={"verbose_name": "Experiment Date", "required": True, "std_unit": None},
    )
    d_to_g = Column(Float, info={"verbose_name": "Weighted D/G", "std_unit": None})
    gp_to_g = Column(Float, info={"verbose_name": "Weighted G'/G", "std_unit": None})
    d_peak_shift = Column(
        Float,
        info={
            "verbose_name": "Weighted D Peak Shift",
            "std_unit": "cm^-1",
            "required": False,
        },
    )
    d_peak_amplitude = Column(
        Float,
        info={
            "verbose_name": "Weighted D Peak Amplitude",
            "std_unit": None,
            "required": False,
        },
    )
    d_fwhm = Column(
        Float,
        info={
            "verbose_name": "Weighted D FWHM",
            "std_unit": "cm^-1",
            "required": False,
        },
    )
    g_peak_shift = Column(
        Float,
        info={
            "verbose_name": "Weighted G Peak Shift",
            "std_unit": "cm^-1",
            "required": False,
        },
    )
    g_peak_amplitude = Column(
        Float,
        info={
            "verbose_name": "Weighted G Peak Amplitude",
            "std_unit": None,
            "required": False,
        },
    )
    g_fwhm = Column(
        Float,
        info={
            "verbose_name": "Weighted G FWHM",
            "std_unit": "cm^-1",
            "required": False,
        },
    )
    g_prime_peak_shift = Column(
        Float,
        info={
            "verbose_name": "Weighted G' Peak Shift",
            "std_unit": "cm^-1",
            "required": False,
        },
    )
    g_prime_peak_amplitude = Column(
        Float,
        info={
            "verbose_name": "Weighted G' Peak Amplitude",
            "std_unit": None,
            "required": False,
        },
    )
    g_prime_fwhm = Column(
        Float,
        info={
            "verbose_name": "Weighted G' FWHM",
            "std_unit": "cm^-1",
            "required": False,
        },
    )

    def json_encodable(self):
        params = [
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
        json_dict["authors"] = [s.json_encodable() for s in self.authors]
        json_dict["experiment_date"] = self.experiment_date.timetuple()
        json_dict["raman_spectra"] = [r.json_encodable() for r in self.raman_spectra]
        json_dict["d_to_g"] = {"value:": getattr(self, "d_to_g"), "unit": None}
        json_dict["gp_to_g"] = {"value:": getattr(self, "gp_to_g"), "unit": None}
        for p in params:
            json_dict[p] = {
                "value": getattr(self, p),
                "unit": getattr(RamanSpectrum, p).info["std_unit"],
            }

        return json_dict
