
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from contextlib import contextmanager
from . config import Config
import ast

Base = declarative_base()

class DataAccessLayer:

    def __init__(self):
        """ Define data access layer attrubutes."""
        self.engine = None
        self.Session = None 
        
#engine = create_engine('mysql+mysqlconnector://'+db_user+':'+db_pass+'@'+db_url, connect_args=ssl_args)

    def init_db(self,config):
        """Initialize database connection.

        The current initializer is specific for mysql+mysqlconnector with SSL arguments.
        Future version of this should be bable to initiate non-SSL connection with any connector.
        """
        #print(config.DATABASEURI)
        #print(config.DATABASEARGS)
        if (config.DATABASEARGS == None):
            self.engine = create_engine(config.DATABASEURI)
        else:
            self.engine = create_engine(config.DATABASEURI,connect_args=ast.literal_eval(config.DATABASEARGS))
        Base.metadata.create_all(bind=self.engine)
        self.Session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=self.engine))
        Base.query = self.Session.query_property()


    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


dal = DataAccessLayer()

from sqlalchemy import Column, String, Integer, Float, Numeric, ForeignKey
from sqlalchemy.orm import relationship, backref

# Declarative classes to define GresQ DB schema
class sample(Base):
    __tablename__ = 'samples'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    material_name = Column(String(32),info={'verbose_name':'Material Name'})
    formula = Column(String(32),info={'verbose_name':'Formula'})
    identifier = Column(String(32),info={'verbose_name':'Identifier'}) # delete
    reference = Column(String(32),info={'verbose_name':'Reference'}) # change to doi

    # CONDITION ALL parameters:
    catalyst = Column(String(64),info={'verbose_name':'Catalyst'})
    tube_diameter = Column(Float(precision=32),info={'verbose_name':'Tube Diameter'})
    cross_sectional_area = Column(Float,info={'verbose_name':'Cross Sectional Area'})
    tube_length = Column(Float,info={'verbose_name':'Tube Length'})
    base_pressure = Column(Float,info={'verbose_name':'Base Pressure'})

    # PROPERTIES
    average_thickness_of_growth = Column(Float(precision=32),info={'verbose_name':'Average Thickness of Growth'})
    standard_deviation_of_growth = Column(Float,info={'verbose_name':'St. Dev. of Growth'})
    number_of_layers = Column(Integer,info={'verbose_name':'Number of Layers'})
    growth_coverage = Column(Float,info={'verbose_name':'Growth Coverage'})
    domain_size = Column(Float,info={'verbose_name':'Domain Size'})
    geometry = Column(String(32),info={'verbose_name':'Geometry'})
    silicon_peak_shift = Column(Float,info={'verbose_name':'Silicon Peak Shift'})
    silicon_peak_amplitude = Column(Float,info={'verbose_name':'Silicon Peak Amplitude'})
    silicon_fwhm = Column(Float,info={'verbose_name':'Silicon FWHM'})
    d_peak_shift = Column(Float,info={'verbose_name':'D Peak Shift'})
    d_peak_amplitude = Column(Float,info={'verbose_name':'D Peak Amplitude'})
    d_fwhm = Column(Float,info={'verbose_name':"D FWHM"})
    g_peak_shift = Column(Float,info={'verbose_name':'G Peak Shift'})
    g_peak_amplitude = Column(Float,info={'verbose_name':'G Peak Amplitude'})
    g_fwhm = Column(Float,info={'verbose_name':'G FWHM'})
    g_prime_peak_shift = Column(Float,info={'verbose_name':'G\' Peak Shift'})
    g_prime_peak_amplitude = Column(Float, info={'verbose_name':'G\' Peak Amplitude'})
    g_prime_fwhm = Column(Float,info={'verbose_name':'G\' FWHM'})
    lorenztians_under_g_prime_peak = Column(Integer,info={'verbose_name':'Number of Lorentzians Under G\' Peak'})
    sample_surface_area = Column(Float,info={'verbose_name':'Sample Surface Area'})
    thickness = Column(Float,info={'verbose_name':'Thickness'})
    diameter = Column(Float,info={'verbose_name':'Diameter'})
    length = Column(Float,info={'verbose_name':'Length'})

    preparation_steps = relationship("preparation_step")

    def json_encodable(self):
        return {
            "material_name": self.material_name,
            "formula": self.formula,
            "identifier": self.identifier,

            "catalyst": self.catalyst,
            "tube_diameter": self.tube_diameter,
            "cross_sectional_area": self.cross_sectional_area,
            "tube_length": self.tube_length,
            "base_pressure": self.base_pressure,

            "average_thickness_of_growth": self.average_thickness_of_growth,
            "standard_deviation_of_growth": self.standard_deviation_of_growth,
            "number_of_layers": self.number_of_layers,
            "growth_coverage": self.growth_coverage,
            "domain_size": self.domain_size,
            "geometry": self.geometry,
            "silicon_peak_shift": self.silicon_peak_shift,
            "silicon_peak_amplitude": self.silicon_peak_amplitude,
            "silicon_fwhm": self.silicon_fwhm,
            "d_peak_shift": self.d_peak_shift,
            "d_peak_amplitude": self.d_peak_amplitude,
            "d_fwhm": self.d_fwhm,
            "g_peak_shift": self.g_peak_shift,
            "g_peak_amplitude": self.g_peak_amplitude,
            "g_fwhm": self.g_fwhm,
            "g_prime_peak_shift": self.g_prime_peak_shift,
            "g_prime_peak_amplitude": self.g_prime_peak_amplitude,
            "g_prime_fwhm": self.g_prime_fwhm,
            "lorenztians_under_g_prime_peak": self.lorenztians_under_g_prime_peak,
            "sample_surface_area": self.sample_surface_area,
            "thickness": self.thickness,
            "diameter": self.diameter,
            "length": self.length,
            "annealing_steps": sorted([s.json_encodable() for s in
                                self.annealing_steps], key= lambda s: s["timestamp"]),
            "growing_steps": sorted([s.json_encodable() for s in
                                self.growing_steps], key= lambda s: s["timestamp"]),
            "cooling_steps": sorted([s.json_encodable() for s in
                                self.cooling_steps], key= lambda s: s["timestamp"])
        }



class preparation_step(Base):
    __tablename__ = 'preparation_steps'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True,info={'verbose_name':'Sample ID'})
    name = Column(String(16),primary_key=True,info={'verbose_name':'Name'})
    timestamp = Column(Integer,info={'verbose_name':'Timestamp'})
    furnace_temperature = Column(Float,info={'verbose_name':'Furnace Temperature'})
    furnace_pressure = Column(Float,info={'verbose_name':'Furnace Pressure'})
    sample_location = Column(Float,info={'verbose_name':'Sample Location'})
    helium_flow_rate = Column(Float,info={'verbose_name':'Helium Flow Rate'})
    hydrogen_flow_rate = Column(Float,info={'verbose_name':'Hydrogen Flow Rate'})
    carbon_source = Column(String(16),info={'verbose_name':'Carbon Source'})
    carbon_source_flow_rate = Column(Float,info={'verbose_name':'Carbon Source Flow Rate'})
    argon_flow_rate = Column(Float,info={'verbose_name':'Argon Flow Rate'})
    cooling_rate = Column(Float,info={'verbose_name':'Cooling Rate'})
    step = Column(Integer,primary_key=True,info={'verbose_name':'Step'})

    #sample = relationship("sample", back_populates="preparation_steps")

    def json_encodable(self):
        rslt = {
            "timestamp": self.timestamp,
            "furnace_temperature": self.furnace_temperature,
            "furnace_pressure": self.furnace_pressure,
            "sample_location": self.sample_location,
            "helium_flow_rate": self.helium_flow_rate,
            "hydrogen_flow_rate": self.hydrogen_flow_rate,
            "carbon_source": self.carbon_source,
            "carbon_source_flow_rate": self.carbon_source_flow_rate,
            "argon_flow_rate": self.argon_flow_rate,
        }

        if self.name == "Cooling":
            rslt["cooling_rate"] = self.cooling_rate

        return rslt


class image(Base):
    __tablename__ = 'images'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    type = Column(String(16),primary_key=True)
    filename = Column(String(16),primary_key=True)
    location = Column(String(256))
    size = Column(Integer)
    hash = Column(String(128))


from json import JSONEncoder


class GresqEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, 'json_encodable'):
            return o.json_encodable()
        else:
            raise TypeError(
                'Object of type %s with value of %s is not JSON serializable' % (
                    type(o), repr(o)))

