
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

from sqlalchemy import Column, String, Integer, Float, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref

# Declarative classes to define GresQ DB schema
class sample(Base):
    __tablename__ = 'samples'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    authors = relationship("author")
    material_name = Column(String(32),info={
        'verbose_name':'Material Name',
        'choices': ['Graphene']
        })

    # EXPERIMENTAL CONDITIONS:
    catalyst = Column(String(64),info={'verbose_name':'Catalyst', 'choices':[]})
    tube_diameter = Column(Float(precision=32),info={
        'verbose_name':'Tube Diameter',
        'std_unit':'mm',
        'conversions': {'mm':1,'inches':25.4}
        })
    cross_sectional_area = Column(Float,info={
        'verbose_name':'Cross Sectional Area',
        'std_unit': 'mm^2',
        'conversions': {'mm^2':1,'inches^2':25.4**2}
        })
    tube_length = Column(Float,info={
        'verbose_name':'Tube Length',
        'std_unit': 'mm',
        'conversions': {'mm':1,'inches':25.4}
        })
    base_pressure = Column(Float,info={
        'verbose_name':'Base Pressure',
        'std_unit': 'mTorr',
        'conversions': {'mTorr':1,'Pa':1/133.322,'mbar':1/1.33322}
        })

    # GRAPHENE PROPERTIES
    average_thickness_of_growth = Column(Float(precision=32),info={
        'verbose_name':'Average Thickness of Growth',
        'std_unit': 'nm',
        'conversions':{'nm':1}
        })
    standard_deviation_of_growth = Column(Float,info={
        'verbose_name':'St. Dev. of Growth',
        'std_unit': 'nm',
        'conversions':{'nm':1}
        })
    number_of_layers = Column(Integer,info={'verbose_name':'Number of Layers'})
    growth_coverage = Column(Float,info={
        'verbose_name':'Growth Coverage',
        'std_unit': '%',
        'conversions':{'%':1}
        })
    domain_size = Column(Float,info={
        'verbose_name':'Domain Size',
        'std_unit': 'um^2',
        'conversions':{'um^2':1}
        })
    shape = Column(String(32),info={
        'verbose_name':'Shape',
        'choices': ['Hexagonal','Square','Circle','Nondescript']
        })

    # # RAMAN


    # SUBSTRATE
    thickness = Column(Float,info=
        {'verbose_name':'Thickness',
        'std_unit':'um',
        'conversions':{'um':1}
        })
    diameter = Column(Float,info=
        {'verbose_name':'Diameter',
        'std_unit':'um',
        'conversions':{'um':1}
        })
    length = Column(Float,info=
        {'verbose_name':'Length',
        'std_unit':'um',
        'conversions':{'um':1}
        })
    # sample_surface_area = Column(Float,info=
    #     {'verbose_name':'Sample Surface Area',
    #     'std_unit': 'um^2',
    #     'conversions':{'um^2':1}
    #     })

    # PREPARATION STEPS
    preparation_steps = relationship("preparation_step")

    def json_encodable(self):
        return {
            "material_name": self.material_name,
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
            "shape": self.shape,
            # "sample_surface_area": self.sample_surface_area,
            "thickness": self.thickness,
            "diameter": self.diameter,
            "length": self.length,
            "preparation_steps": sorted([s.json_encodable() for s in
                                self.preparation_steps if s.timestamp] , key= lambda s: s["timestamp"]),
            "authors": [s.json_encodable() for s in self.authors]
        }



class preparation_step(Base):
    __tablename__ = 'preparation_steps'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True,info={'verbose_name':'Sample ID'})
    name = Column(String(16),primary_key=True,info={
        'verbose_name':'Name',
        'choices': ['Annealing','Growing','Cooling']
        })
    timestamp = Column(Float,primary_key=True,info={
        'verbose_name':'Timestamp',
        'std_unit': 'min',
        'conversions': {'min':1,'sec':1/60.,'hrs':60}
        })
    furnace_temperature = Column(Float,info={
        'verbose_name':'Furnace Temperature',
        'std_unit': 'C',
        'conversions': {'C':1}
        })
    furnace_pressure = Column(Float,info={
        'verbose_name':'Furnace Pressure',
        'std_unit': 'mTorr',
        'conversions': {'mTorr':1,'Pa':1/133.322,'mbar':1/1.33322}
        })
    sample_location = Column(Float,info={
        'verbose_name':'Sample Location',
        'std_unit':'mm',
        'conversions': {'inches':25.4,'mm':1}
        })
    helium_flow_rate = Column(Float,info={
        'verbose_name':'Helium Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1}
        })
    hydrogen_flow_rate = Column(Float,info={
        'verbose_name':'Hydrogen Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1}
        })
    carbon_source = Column(String(16),info={
        'verbose_name':'Carbon Source',
        'choices': ['CH4','C2H4','C2H2','C6H6']
        })
    carbon_source_flow_rate = Column(Float,info={
        'verbose_name':'Carbon Source Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1}
        })
    argon_flow_rate = Column(Float,info={
        'verbose_name':'Argon Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1}
        })
    cooling_rate = Column(Float,info={
        'verbose_name':'Cooling Rate',
        'std_unit': 'C/min',
        'conversions': {'C/min':1}
        })

    #sample = relationship("sample", back_populates="preparation_steps")

    def json_encodable(self):
        rslt = {
            "name": self.name,
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

class author(Base):
    __tablename__ = 'author'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True,info={'verbose_name':'Sample ID'})
    first_name = Column(String(64), primary_key=True, info={'verbose_name':'First Name'})
    last_name = Column(String(64), primary_key=True, info={'verbose_name':'Last Name'})
    institution = Column(String(64), primary_key=True, info={'verbose_name':'Institution'})

    def json_encodable(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'institution': self.institution
        }

class raman_spectrum(Base):
    __tablename__ = 'raman_spectrum'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True,info={'verbose_name':'Sample ID'})
    wavelength = Column(Float,info={
        'verbose_name':'Wavelength',
        'std_unit': 'Hz',
        'conversions': {'Hz':1}
        })
    percent = Column(Float,info={
        'verbose_name':'Characteristic Percent',
        'std_unit': '%',
        'conversions': {'%':1}
        })
    d_peak_shift = Column(Float,info={
        'verbose_name':'D Peak Shift',
        'std_unit': 'cm^-1'
        })
    d_peak_amplitude = Column(Float,info={'verbose_name':'D Peak Amplitude'})
    d_fwhm = Column(Float,info={
        'verbose_name':"D FWHM",
        'std_unit': 'cm^-1'
        })
    g_peak_shift = Column(Float,primary_key=True,info={
        'verbose_name':'G Peak Shift',
        'std_unit': 'cm^-1'
        })
    g_peak_amplitude = Column(Float,primary_key=True,info={'verbose_name':'G Peak Amplitude'})
    g_fwhm = Column(Float,primary_key=True,info={
        'verbose_name':'G FWHM',
        'std_unit': 'cm^-1'
        })
    g_prime_peak_shift = Column(Float,info={
        'verbose_name':'G\' Peak Shift',
        'std_unit': 'cm^-1'
        })
    g_prime_peak_amplitude = Column(Float, info={'verbose_name':'G\' Peak Amplitude'})
    g_prime_fwhm = Column(Float,info={
        'verbose_name':'G\' FWHM',
        'std_unit': 'cm^-1'
        })

    def json_encodable(self):
        rslt = {
            "wavelength": self.wavelength,
            "percent": self.percent,
            "d_peak_shift": self.d_peak_shift,
            "d_peak_amplitude": self.d_peak_amplitude,
            "d_fwhm": self.d_fwhm,
            "g_peak_shift": self.g_peak_shift,
            "g_peak_amplitude": self.g_peak_amplitude,
            "g_fwhm": self.g_fwhm,
            "g_prime_peak_shift": self.g_prime_peak_shift,
            "g_prime_peak_amplitude": self.g_prime_peak_amplitude,
            "g_prime_fwhm": self.g_prime_fwhm,
        }

        return rslt

class image(Base):
    __tablename__ = 'images'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    type = Column(String(16),primary_key=True)
    filename = Column(String(16),primary_key=True)
    location = Column(String(256))
    size = Column(Integer)
    hash = Column(String(128))


class mdf_forge(Base):
    __tablename__ = 'mdf_forge'
    mdf_id = Column(String(32),primary_key=True,info={'verbose_name':'MDF ID'})
    title = Column(String(64), info={'verbose_name':'Title'})
    catalyst = Column(String(32),info={'verbose_name':'Catalyst'})
    max_temperature = Column(Integer,info={'verbose_name':'Maximum Temperature'})
    carbon_source = Column(String(32),info={'verbose_name':'Carbon Source'})
    base_pressure = Column(Float,info={'verbose_name':'Base Pressure'})

    sample_surface_area = Column(Float,info={'verbose_name':'Sample Surface Area'})
    sample_thickness = Column(Float,info={'verbose_name':'Sample Thickness'})

    orientation = Column(Float,info={'verbose_name':'Orientation'})
    grain_size = Column(Float,info={'verbose_name':'Grain Size'})


from json import JSONEncoder


class GresqEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, 'json_encodable'):
            return o.json_encodable()
        else:
            raise TypeError(
                'Object of type %s with value of %s is not JSON serializable' % (
                    type(o), repr(o)))

