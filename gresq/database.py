
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
    id = Column(Integer,primary_key=True)
    material_name = Column(String(32))
    formula = Column(String(32))
    identifier = Column(String(32))
    reference = Column(String(32))

    # CONDITION ALL parameters:
    catalyst = Column(String(64))
    tube_diameter = Column(Float(precision=32))
    cross_sectional_area = Column(Float)
    tube_length = Column(Float)
    base_pressure = Column(Float)

    # PROPERTIES
    average_thickness_of_growth = Column(Float(precision=32))
    standard_deviation_of_growth = Column(Float)
    number_of_layers = Column(Integer)
    growth_coverage = Column(Float)
    domain_size = Column(Float)
    geometry = Column(String(32))
    silicon_peak_shift = Column(Float)
    silicon_peak_amplitude = Column(Float)
    silicon_fwhm = Column(Float)
    d_peak_shift = Column(Float)
    d_peak_amplitude = Column(Float)
    d_fwhm = Column(Float)
    g_peak_shift = Column(Float)
    g_peak_amplitude = Column(Float)
    g_fwhm = Column(Float)
    g_prime_peak_shift = Column(Float)
    g_prime_peak_amplitude = Column(Float)
    g_prime_fwhm = Column(Float)
    lorenztians_under_g_prime_peak = Column(Integer)
    sample_surface_area = Column(Float)
    thickness = Column(Float)
    diameter = Column(Float)
    length = Column(Float)

    #preparation_steps = relationship("preparation_step",back_populates="samples")

class preparation_step(Base):
    __tablename__ = 'preparation_steps'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    name = Column(String(16),primary_key=True)
    timestamp = Column(Integer,primary_key=True)
    furnace_temperature = Column(Float)
    furnace_pressure = Column(Float)
    sample_location = Column(Float)
    helium_flow_rate = Column(Float)
    helium_flow_rate = Column(Float)
    hydrogen_flow_rate = Column(Float)
    hydrogen_flow_rate = Column(Float)
    carbon_source = Column(Float)
    carbon_source_flow_rate = Column(Float)
    carbon_source_flow_rate = Column(Float)
    argon_flow_rate = Column(Float)
    argon_flow_rate = Column(Float)
    cooling_rate = Column(Float)

    #sample = relationship("sample", back_populates="preparation_steps")

class image(Base):
    __tablename__ = 'images'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    type = Column(String(16),primary_key=True)
    filename = Column(String(16),primary_key=True)
    location = Column(String(256))
    size = Column(Integer)
    hash = Column(String(128))

class citrine_csv_map(Base):
    __tablename__ = 'citrine_csv_map'
    table = Column(String(32),primary_key=True)
    table_column_name = Column(String(128),primary_key=True)
    csv_column_name = Column(String(128))

