
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from contextlib import contextmanager
from . config import Config
import ast, datetime

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

from sqlalchemy import Column, String, Integer, Float, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship, backref

# Declarative classes to define GresQ DB schema

class sample(Base):
    __tablename__ = 'sample'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    authors = relationship("author")
    experiment_date = Column(Date,default=datetime.date.today,info={
        'verbose_name':'Experiment Date',
        'required':True})
    material_name = Column(String(32),info={
        'verbose_name':'Material Name',
        'choices': ['Graphene'],
        'required': True
        })
    recipe = relationship("recipe",uselist=False)
    properties = relationship("properties",uselist=False)
    sem_files = relationship("sem_file")
    raman_files = relationship("raman_file")

    def json_encodable(self):
        return {
            "material_name": self.material_name,
            "experiment_date":self.experiment_date.timetuple(),
            "authors": [s.json_encodable() for s in self.authors],
            "recipe": self.recipe.json_encodable(),
            "properties": self.properties.json_encodable()
        }

class recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id),info={'verbose_name':'Sample ID'})
    # SUBSTRATE
    thickness = Column(Float,info=
        {'verbose_name':'Thickness',
        'std_unit':'um',
        'conversions':{'um':1},
        'required': False
        })
    diameter = Column(Float,info=
        {'verbose_name':'Diameter',
        'std_unit':'um',
        'conversions':{'um':1},
        'required': False
        })
    length = Column(Float,info=
        {'verbose_name':'Length',
        'std_unit':'um',
        'conversions':{'um':1},
        'required': False
        })

    # EXPERIMENTAL CONDITIONS:
    catalyst = Column(String(64),info={
        'verbose_name':'Catalyst', 
        'choices':[],
        'std_unit':None,
        'required': True})
    tube_diameter = Column(Float(precision=32),info={
        'verbose_name':'Tube Diameter',
        'std_unit':'mm',
        'conversions': {'mm':1,'inches':25.4},
        'required': False
        })
    cross_sectional_area = Column(Float,info={
        'verbose_name':'Cross Sectional Area',
        'std_unit': 'mm^2',
        'conversions': {'mm^2':1,'inches^2':25.4**2},
        'required': False
        })
    tube_length = Column(Float,info={
        'verbose_name':'Tube Length',
        'std_unit': 'mm',
        'conversions': {'mm':1,'inches':25.4},
        'required': False
        })
    base_pressure = Column(Float,info={
        'verbose_name':'Base Pressure',
        'std_unit': 'mTorr',
        'conversions': {'mTorr':1,'Pa':1/133.322,'mbar':1/1.33322},
        'required': True
        })

    # PREPARATION STEPS
    preparation_steps = relationship("preparation_step")

    def json_encodable(self):
        params = [
            "catalyst",
            "tube_diameter",
            "cross_sectional_area",
            "tube_length",
            "base_pressure",
            "thickness",
            "diameter",
            "length"
            ]
        json_dict = {}
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(recipe,p).info['std_unit']}
        json_dict['preparation_steps'] = sorted([s.json_encodable() for s in self.preparation_steps if s.step] , key= lambda s: s["step"])

        return json_dict

class preparation_step(Base):
    __tablename__ = 'preparation_step'
    recipe_id = Column(Integer,ForeignKey(recipe.id),primary_key=True,info={'verbose_name':'Recipe ID'})
    step = Column(Integer,primary_key=True)
    name = Column(String(16),primary_key=True,info={
        'verbose_name':'Name',
        'choices': ['Annealing','Growing','Cooling'],
        'std_unit': None,
        'required': True
        })
    duration = Column(Float,primary_key=True,info={
        'verbose_name':'Duration',
        'std_unit': 'min',
        'conversions': {'min':1,'sec':1/60.,'hrs':60},
        'required': True
        })
    furnace_temperature = Column(Float,info={
        'verbose_name':'Furnace Temperature',
        'std_unit': 'C',
        'conversions': {'C':1},
        'required': True
        })
    furnace_pressure = Column(Float,info={
        'verbose_name':'Furnace Pressure',
        'std_unit': 'mTorr',
        'conversions': {'mTorr':1,'Pa':1/133.322,'mbar':1/1.33322},
        'required': True
        })
    sample_location = Column(Float,info={
        'verbose_name':'Sample Location',
        'std_unit':'mm',
        'conversions': {'inches':25.4,'mm':1},
        'required': False
        })
    helium_flow_rate = Column(Float,info={
        'verbose_name':'Helium Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1},
        'required': False
        })
    hydrogen_flow_rate = Column(Float,info={
        'verbose_name':'Hydrogen Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1},
        'required': False
        })
    carbon_source = Column(String(16),info={
        'verbose_name':'Carbon Source',
        'std_unit': None,
        'choices': ['CH4','C2H4','C2H2','C6H6'],
        'required': True
        })
    carbon_source_flow_rate = Column(Float,info={
        'verbose_name':'Carbon Source Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1},
        'required': True
        })
    argon_flow_rate = Column(Float,info={
        'verbose_name':'Argon Flow Rate',
        'std_unit': 'sccm',
        'conversions': {'sccm':1},
        'required': False
        })
    cooling_rate = Column(Float,info={
        'verbose_name':'Cooling Rate',
        'std_unit': 'C/min',
        'conversions': {'C/min':1},
        'required': False
        })

    #sample = relationship("sample", back_populates="preparation_steps")

    def json_encodable(self):
        params = [
            "name",
            "duration",
            "furnace_temperature",
            "furnace_pressure",
            "sample_location",
            "helium_flow_rate",
            "hydrogen_flow_rate",
            "carbon_source",
            "carbon_source_flow_rate",
            "argon_flow_rate"
            ] 

        if self.name == "Cooling":
            params.append('cooling_rate')

        json_dict = {}
        json_dict['step'] = self.step
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(preparation_step,p).info['std_unit']}

        return json_dict

class author(Base):
    __tablename__ = 'author'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey('sample.id'),info={'verbose_name':'Sample ID'})
    raman_id = Column(Integer,ForeignKey('raman_set.id'),info={'verbose_name':'Raman Set ID'})
    first_name = Column(String(64), info={
        'verbose_name':'First Name',
        'required': False})
    last_name = Column(String(64), info={
        'verbose_name':'Last Name',
        'required': False})
    institution = Column(String(64), info={'verbose_name':'Institution'})

    def json_encodable(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'institution': self.institution
        }

class properties(Base):
    __tablename__ = 'properties'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id),info={'verbose_name':'Sample ID'})
    average_thickness_of_growth = Column(Float(precision=32),info={
        'verbose_name':'Average Thickness of Growth',
        'std_unit': 'nm',
        'conversions':{'nm':1},
        'required': False
        })
    standard_deviation_of_growth = Column(Float,info={
        'verbose_name':'St. Dev. of Growth',
        'std_unit': 'nm',
        'conversions':{'nm':1},
        'required': False
        })
    number_of_layers = Column(Integer,info={
        'verbose_name':'Number of Layers',
        'std_unit':None,
        'required': False})
    growth_coverage = Column(Float,info={
        'verbose_name':'Growth Coverage',
        'std_unit': '%',
        'conversions':{'%':1},
        'required': False
        })
    domain_size = Column(Float,info={
        'verbose_name':'Domain Size',
        'std_unit': 'um^2',
        'conversions':{'um^2':1},
        'required': False
        })
    shape = Column(String(32),info={
        'verbose_name':'Shape',
        'choices': ['Nondescript','Hexagonal','Square','Circle'],
        'std_unit':None,
        'required': False
        })

    def json_encodable(self):
        params = [
            "average_thickness_of_growth",
            "standard_deviation_of_growth",
            "number_of_layers",
            "growth_coverage",
            "domain_size",
            "shape"
            ]
        json_dict = {}
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(properties,p).info['std_unit']}
        return json_dict

class raman_set(Base):
    __tablename__ = 'raman_set'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    raman_spectra = relationship("raman_spectrum")
    authors = relationship("author")
    d_to_g = Column(Float,info={'verbose_name':'Weighted D/G'})
    gp_to_g = Column(Float,info={'verbose_name':'Weighted G\'/G'})
    d_peak_shift = Column(Float,info={
        'verbose_name':'Weighted D Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    d_peak_amplitude = Column(Float,info={
        'verbose_name':'Weighted D Peak Amplitude',
        'std_unit':None,
        'required': False})
    d_fwhm = Column(Float,info={
        'verbose_name':"Weighted D FWHM",
        'std_unit': 'cm^-1',
        'required': False
        })
    g_peak_shift = Column(Float,info={
        'verbose_name':'Weighted G Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_peak_amplitude = Column(Float,info={
        'verbose_name':'Weighted G Peak Amplitude',
        'std_unit':None,
        'required': False})
    g_fwhm = Column(Float,info={
        'verbose_name':'Weighted G FWHM',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_prime_peak_shift = Column(Float,info={
        'verbose_name':'Weighted G\' Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_prime_peak_amplitude = Column(Float, info={
        'verbose_name':'Weighted G\' Peak Amplitude',
        'std_unit':None,
        'required': False})
    g_prime_fwhm = Column(Float,info={
        'verbose_name':'Weighted G\' FWHM',
        'std_unit': 'cm^-1',
        'required': False
        })

    def json_encodable(self):
        params = [
            "d_to_g",
            "gp_to_g",
            "d_peak_shift",
            "d_peak_amplitude",
            "d_fwhm",
            "g_peak_shift",
            "g_peak_amplitude",
            "g_fwhm",
            "g_prime_peak_shift",
            "g_prime_peak_amplitude",
            "g_prime_fwhm"
        ]
        json_dict = {}
        json_dict["authors"] = [s.json_encodable() for s in self.authors]
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(raman_spectrum,p).info['std_unit']}

        return json_dict

class raman_file(Base):
    __tablename__ = 'raman_file'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id))
    filename = Column(String(64))
    wavelength = Column(Float,info={
        'verbose_name':'Wavelength',
        'std_unit': 'nm',
        'conversions': {'nm':1},
        'required': True
        })

    def json_encodable(self):
        params = [
            'wavelength'
        ]
        json_dict = {}
        json_dict['filename'] = self.filename
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(raman_spectrum,p).info['std_unit']}
        return json_dict

class raman_spectrum(Base):
    __tablename__ = 'raman_spectrum'
    set_id = Column(Integer,ForeignKey(raman_set.id),info={'verbose_name':'Sample ID'})
    raman_file_id = Column(Integer,ForeignKey(raman_file.id),primary_key=True)
    raman_file = relationship("raman_file",uselist=False)
    percent = Column(Float,info={
        'verbose_name':'Characteristic Percent',
        'std_unit': '%',
        'conversions': {'%':1},
        'required': True
        })
    d_peak_shift = Column(Float,info={
        'verbose_name':'D Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    d_peak_amplitude = Column(Float,info={
        'verbose_name':'D Peak Amplitude',
        'std_unit':None,
        'required': False})
    d_fwhm = Column(Float,info={
        'verbose_name':"D FWHM",
        'std_unit': 'cm^-1',
        'required': False
        })
    g_peak_shift = Column(Float,info={
        'verbose_name':'G Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_peak_amplitude = Column(Float,info={
        'verbose_name':'G Peak Amplitude',
        'std_unit':None,
        'required': False})
    g_fwhm = Column(Float,info={
        'verbose_name':'G FWHM',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_prime_peak_shift = Column(Float,info={
        'verbose_name':'G\' Peak Shift',
        'std_unit': 'cm^-1',
        'required': False
        })
    g_prime_peak_amplitude = Column(Float, info={
        'verbose_name':'G\' Peak Amplitude',
        'std_unit':None,
        'required': False})
    g_prime_fwhm = Column(Float,info={
        'verbose_name':'G\' FWHM',
        'std_unit': 'cm^-1',
        'required': False
        })

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
            "g_prime_fwhm"
        ]
        json_dict = {}
        json_dict['raman_file'] = self.raman_file.json_encodable()
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(raman_spectrum,p).info['std_unit']}

        return json_dict

class image(Base):
    __tablename__ = 'images'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    type = Column(String(16),primary_key=True)
    filename = Column(String(16),primary_key=True)
    location = Column(String(256))
    size = Column(Integer)
    hash = Column(String(128))

class sem_file(Base):
    __tablename__ = 'sem_file'
    sample_id = Column(Integer,ForeignKey(sample.id),primary_key=True)
    filename = Column(String(64),primary_key=True)

    def json_encodable(self):
        return {'filename': self.filename}

class mdf_forge(Base):
    __tablename__ = 'mdf_forge'
    mdf_id = Column(String(32),primary_key=True,info={'verbose_name':'MDF ID'})
    title = Column(String(64), info={'verbose_name':'Title'})
    catalyst = Column(String(32),info={'verbose_name':'Catalyst'})
    max_temperature = Column(Float,info={'verbose_name':'Maximum Temperature'})
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

