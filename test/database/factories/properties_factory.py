import factory

from gresq.database.models import Properties
from gresq.database.dal import dal

from .. import test_session


LIST_SIZES = [1, 2, 3, 4, 5, 6]

class PropertiesFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Properties
        #sqlalchemy_session = dal.Session()
        sqlalchemy_session = test_session
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", properties=None)

    average_thickness_of_growth = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    standard_deviation_of_growth = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    number_of_layers = factory.Faker("pyint", min_value=0, max_value=3, step=1)
    growth_coverage = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=100.0)
    domain_size = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    shape = factory.Iterator(Properties.shape.info["choices"])

