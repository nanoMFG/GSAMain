
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
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
    identifier = Column(String(32),info={'verbose_name':'Identifier'})
    reference = Column(String(32),info={'verbose_name':'Reference'})

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

class image(Base):
    __tablename__ = 'images'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    type = Column(String(16),primary_key=True)
    filename = Column(String(16),primary_key=True)
    location = Column(String(256))
    size = Column(Integer)
    hash = Column(String(128))