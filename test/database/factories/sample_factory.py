import factory
import random

from gresq.database.models import Sample
from gresq.database.dal import dal

LIST_SIZES = [1, 2, 3, 4, 5, 6]

class SampleFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Sample
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    #id = factory.Sequence(lambda n: n)
    recipe = factory.RelatedFactory("test.database.factories.RecipeFactory", "sample")
    properties = factory.RelatedFactory("test.database.factories.PropertiesFactory", "sample")
    author = factory.RelatedFactoryList("test.database.factories.AuthorFactory", "sample",
                                     size=lambda: LIST_SIZES[random.randint(0,5)])
    #author = factory.RelatedFactory("test.database.factories.AuthorFactory")

    nanohub_userid = factory.Faker("pyint", min_value=0, max_value=9999, step=1)
    experiment_date = factory.Faker("date")
    material_name = factory.Iterator(Sample.material_name.info["choices"])
    validated = factory.Faker("boolean", chance_of_getting_true=50)

    