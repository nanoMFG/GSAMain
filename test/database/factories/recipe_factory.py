import factory
import random

from gresq.database.models import Recipe
from gresq.database.dal import dal

from .. import test_session


LIST_SIZES = [1, 2, 3, 4, 5, 6]

class RecipeFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Recipe
        #sqlalchemy_session = dal.Session()
        sqlalchemy_session = test_session
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", recipe=None)
    preparation_steps = factory.RelatedFactoryList("test.database.factories.PreparationStepFactory", "recipe",
                                     size=3)

    thickness = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=99.0)
    diameter = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    length = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    catalyst = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    tube_diameter = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    cross_sectional_area = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    tube_length = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    base_pressure = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    dewpoint = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
    sample_surface_area = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=10.0)
   