
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from contextlib import contextmanager
from gresq.config import Config
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext import compiler
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import exists, expression
import ast, datetime
from sqlalchemy import Column, String, Integer, Float, Numeric, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, backref
from gresq.database import Base


class group_concat(expression.FunctionElement):
    name = "group_concat"


@compiler.compiles(group_concat, 'mysql')
def _group_concat_mysql(element, compiler, **kw):
    if len(element.clauses) == 2:
        separator = compiler.process(element.clauses.clauses[1])
    else:
        separator = ', '

    return 'GROUP_CONCAT(%s SEPARATOR %s)'.format(
        compiler.process(element.clauses.clauses[0]),
        separator,
    )

class sample(Base):
    __tablename__ = 'sample'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID','std_unit':None})
    nanohub_userid = Column(Integer,info={'verbose_name':'Nanohub Submitter User ID','std_unit':None})
    authors = relationship("author")
    experiment_date = Column(Date,info={
        'verbose_name':'Experiment Date',
        'required':True,
        'std_unit':None})
    material_name = Column(String(32),info={
        'verbose_name':'Material Name',
        'choices': ['Graphene'],
        'required': True,
        'std_unit':None
        })
    recipe = relationship("recipe",uselist=False,cascade="save-update, merge, delete")
    properties = relationship("properties",uselist=False,cascade="save-update, merge, delete")
    
    raman_analysis = relationship("raman_set",uselist=False,cascade="save-update, merge, delete")
    raman_files = relationship("raman_file",back_populates="sample_id")

    sem_files = relationship("sem_file",cascade="save-update, merge, delete")
    primary_sem_file_id = Column(Integer,ForeignKey("sem_analysis.id",use_alter=True),index=True)
    primary_sem_file = relationship("sem_file",primaryjoin="sem_file.id==primary_sem_file_id",uselist=False)

    validated = Column(Boolean,info={'verbose_name':'Validated','std_unit':None},default=False)

    @hybrid_property
    def primary_sem_analysis(self):
        return self.primary_sem_file.default_analysis

    @hybrid_property
    def sem_analyses(self):
        return [s.default_analysis for s in self.sem_files]

    @hybrid_property
    def author_last_names(self):
        return ', '.join(sorted([a.last_name for a in self.authors if a.last_name]))

    @author_last_names.expression
    def author_last_names(cls): # BROKEN
        selection = select([func.group_concat(author.last_name)]).\
                where(author.sample_id==cls.id).\
                correlate(cls)

    def json_encodable(self):
        return {
            "primary_key": self.id,
            "material_name": self.material_name,
            "experiment_date":self.experiment_date.timetuple(),
            "authors": [s.json_encodable() for s in self.authors],
            "recipe": self.recipe.json_encodable(),
            "properties": self.properties.json_encodable()
        }

class recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id), index=True, info={'verbose_name':'Sample ID'})
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
        'std_unit': 'Torr',
        'conversions': {'Torr':1,'Pa':1/133.322,'mbar':1/1.33322},
        'required': True
        })
    dewpoint = Column(Float,info={
        'verbose_name':'Dew Point',
        'std_unit': 'C',
        'conversions': {'C':1},
        'required': False
        })
    sample_surface_area = Column(Float,info={
        'verbose_name':'Sample Surface Area',
        'std_unit': 'mm^2',
        'conversions':{'mm^2':1},
        'required': False
        })

    @hybrid_property
    def maximum_temperature(self):
        return max([p.furnace_temperature for p in self.preparation_steps if p.furnace_temperature!=None])

    @maximum_temperature.expression
    def maximum_temperature(cls):
        return select([func.max(preparation_step.furnace_temperature)]).\
                where(preparation_step.recipe_id==cls.id).correlate(cls).\
                label('maximum_temperature')

    @hybrid_property
    def maximum_pressure(self):
        return max([p.furnace_pressure for p in self.preparation_steps if p.furnace_pressure!=None])

    @maximum_pressure.expression
    def maximum_pressure(cls):
        return select([func.max(preparation_step.furnace_pressure)]).\
                where(preparation_step.recipe_id==cls.id).correlate(cls).\
                label('maximum_pressure')

    @hybrid_property
    def average_carbon_flow_rate(self):
        steps = [p.carbon_source_flow_rate for p in self.preparation_steps if p.carbon_source_flow_rate!=None]
        return sum(steps)/len(steps)

    @average_carbon_flow_rate.expression
    def average_carbon_flow_rate(cls):
        return select([func.avg(preparation_step.carbon_source_flow_rate)]).\
                where(preparation_step.recipe_id==cls.id).correlate(cls).\
                label('average_carbon_flow_rate')

    @hybrid_property
    def carbon_source(self):
        vals = [p.carbon_source for p in self.preparation_steps if p.carbon_source is not None]
        return vals[0]

    @carbon_source.expression
    def carbon_source(cls):
        return select([preparation_step.carbon_source]).\
                where(and_(preparation_step.recipe_id==cls.id,preparation_step.carbon_source != None)).\
                correlate(cls).\
                limit(1).\
                label('carbon_source')

    @hybrid_property
    def uses_helium(self):
        return any([p.helium_flow_rate for p in self.preparation_steps])

    @uses_helium.expression
    def uses_helium(cls):
        s = select([preparation_step.helium_flow_rate]).\
                where(and_(preparation_step.helium_flow_rate != None,preparation_step.recipe_id==cls.id)).\
                correlate(cls)
        return exists(s)

    @hybrid_property
    def uses_argon(self):
        return any([p.argon_flow_rate for p in self.preparation_steps])

    @uses_argon.expression
    def uses_argon(cls):
        s = select([preparation_step.argon_flow_rate]).\
                where(and_(preparation_step.argon_flow_rate != None,preparation_step.recipe_id==cls.id)).\
                correlate(cls)
        return exists(s)

    @hybrid_property
    def uses_hydrogen(self):
        return any([p.hydrogen_flow_rate for p in self.preparation_steps])

    @uses_hydrogen.expression
    def uses_hydrogen(cls):
        s = select([preparation_step.hydrogen_flow_rate]).\
                where(and_(preparation_step.hydrogen_flow_rate != None,preparation_step.recipe_id==cls.id)).\
                correlate(cls)
        return exists(s)

    # PREPARATION STEPS
    preparation_steps = relationship("preparation_step",cascade="save-update, merge, delete")

    def json_encodable(self):
        params = [
            "catalyst",
            "tube_diameter",
            "cross_sectional_area",
            "tube_length",
            "base_pressure",
            "thickness",
            "diameter",
            "length",
            "dewpoint"
            ]
        json_dict = {}
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(recipe,p).info['std_unit']}
        json_dict['preparation_steps'] = sorted([s.json_encodable() for s in self.preparation_steps if s.step!=None] , key= lambda s: s["step"])

        return json_dict

class preparation_step(Base):
    __tablename__ = 'preparation_step'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    recipe_id = Column(Integer,ForeignKey(recipe.id),info={'verbose_name':'Recipe ID'},index=True)
    step = Column(Integer)
    name = Column(String(16),info={
        'verbose_name':'Name',
        'choices': ['Annealing','Growing','Cooling'],
        'std_unit': None,
        'required': True
        })
    duration = Column(Float,info={
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
        'std_unit': 'Torr',
        'conversions': {'Torr':1,'Pa':1/133.322,'mbar':1/1.33322},
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
    sample_id = Column(Integer,ForeignKey('sample.id'), index=True, info={'verbose_name':'Sample ID'})
    raman_id = Column(Integer,ForeignKey('raman_set.id'), index=True, info={'verbose_name':'Raman Set ID'})
    first_name = Column(String(64), info={
        'verbose_name':'First Name',
        'std_unit': None,
        'required': False})
    last_name = Column(String(64), info={
        'verbose_name':'Last Name',
        'std_unit': None,
        'required': False})
    institution = Column(String(64), info={
        'verbose_name':'Institution',
        'std_unit': None,
        'required': False
        })

    @hybrid_property
    def full_name_and_institution(self):
        return "%s, %s   (%s)"%(self.last_name,self.first_name,self.institution)

    def json_encodable(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'institution': self.institution
        }

class properties(Base):
    __tablename__ = 'properties'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id), index=True, info={'verbose_name':'Sample ID'})
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
    nanohub_userid = Column(Integer,info={'verbose_name':'Nanohub Submitter User ID'})
    map_file = Column(Boolean,info={'verbose_name':'Map File'},default=False)
    sample_id = Column(Integer,ForeignKey(sample.id), index=True, info={'verbose_name':'Sample ID'})
    raman_spectra = relationship("raman_spectrum",cascade="save-update, merge, delete")
    authors = relationship("author")
    experiment_date = Column(Date,default=datetime.date.today,info={
        'verbose_name':'Experiment Date',
        'required':True,
        'std_unit':None})
    d_to_g = Column(Float,info={'verbose_name':'Weighted D/G','std_unit':None})
    gp_to_g = Column(Float,info={'verbose_name':'Weighted G\'/G','std_unit':None})
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
        json_dict["experiment_date"] = self.experiment_date.timetuple()
        json_dict["raman_spectra"] = [r.json_encodable() for r in self.raman_spectra]
        json_dict['d_to_g'] = {'value:':getattr(self,'d_to_g'),'unit':None}
        json_dict['gp_to_g'] = {'value:':getattr(self,'gp_to_g'),'unit':None}
        for p in params:
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(raman_spectrum,p).info['std_unit']}

        return json_dict

class raman_file(Base):
    __tablename__ = 'raman_file'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id), index=True)
    filename = Column(String(64))
    url = Column(String(256))
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
            json_dict[p] = {'value':getattr(self,p),'unit':getattr(raman_file,p).info['std_unit']}
        return json_dict

class raman_spectrum(Base):
    __tablename__ = 'raman_spectrum'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    set_id = Column(Integer,ForeignKey(raman_set.id), index=True, info={'verbose_name':'Raman Set ID'})
    raman_file_id = Column(Integer,ForeignKey(raman_file.id))
    raman_file = relationship("raman_file",uselist=False,cascade="save-update, merge, delete")
    xcoord = Column(Integer,info={'verbose_name':'X Coordinate'})
    ycoord = Column(Integer,info={'verbose_name':'Y Coordinate'})
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

class sem_analysis(Base):
    __tablename__ = 'sem_analysis'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sem_file_id = Column(Integer,ForeignKey("sem_file.id"),index=True)
    sem_file_model = relationship("sem_file",primaryjoin="sem_analysis.sem_file_id==id",back_populates="analyses")

    mask_url = Column(String(256))
    px_per_um = Column(Integer,info={'verbose_name':'Pixels/um'})
    growth_coverage = Column(Float,info={
        'verbose_name':'Growth Coverage',
        'std_unit': '%',
        'conversions':{'%':1},
        'required': False
        })
    automated = Column(Boolean,info={'verbose_name':'Automated Detection','std_unit':None},default=False)

    def json_encodable(self):
        return {
            'growth_coverage': {'value':self.growth_coverage,'unit':'%'},
            'px_per_um': {'value':self.px_per_um,'unit':'1/um'},
            'automated': {'value':self.automated,'unit':None}
            }

class sem_file(Base):
    __tablename__ = 'sem_file'
    id = Column(Integer,primary_key=True,info={'verbose_name':'ID'})
    sample_id = Column(Integer,ForeignKey(sample.id),index=True)
    filename = Column(String(64))
    url = Column(String(256))

    default_analysis_id = Column(Integer,ForeignKey("sem_analysis.id",use_alter=True),index=True)

    default_analysis = relationship("sem_analysis",primaryjoin="sem_analysis.id==default_analysis_id")
    analyses = relationship("sem_analysis",primaryjoin="sem_analysis.sem_file_id==id")

    def json_encodable(self):
        return {
            'filename': self.filename
            }


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


hybrid_recipe_fields = [
    "maximum_temperature",
    "maximum_pressure",
    "average_carbon_flow_rate",
    "carbon_source",
    "uses_helium",
    "uses_hydrogen",
    "uses_argon"
    ]

hybrid_author_fields = [
    "full_name_and_institution"
]

# Hybrid attributes require their info dictionary values be set outside of class construction.

recipe.maximum_temperature.info['verbose_name'] = 'Maximum Temperature'
recipe.maximum_temperature.info['std_unit'] = 'C'

recipe.maximum_pressure.info['verbose_name'] = 'Maximum Pressure'
recipe.maximum_pressure.info['std_unit'] = 'Torr'

recipe.maximum_temperature.info['verbose_name'] = 'Maximum Temperature'
recipe.maximum_temperature.info['std_unit'] = 'C'

recipe.average_carbon_flow_rate.info['verbose_name'] = 'Average Carbon Flow Rate'
recipe.average_carbon_flow_rate.info['std_unit'] = 'sccm'

recipe.carbon_source.info['verbose_name'] = 'Carbon Source'
recipe.carbon_source.info['std_unit'] = None

recipe.uses_helium.info['verbose_name'] = 'Uses Helium'
recipe.uses_helium.info['std_unit'] = None

recipe.uses_argon.info['verbose_name'] = 'Uses Argon'
recipe.uses_argon.info['std_unit'] = None

recipe.uses_hydrogen.info['verbose_name'] = 'Uses Hydrogen'
recipe.uses_hydrogen.info['std_unit'] = None

author.full_name_and_institution.info['verbose_name'] = "Author"
author.full_name_and_institution.info['std_unit'] = None
