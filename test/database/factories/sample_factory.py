import factory
import random

from grdb.database.v1_1_0.models import Sample
from grdb.database.v1_1_0.dal import dal

LIST_SIZES = [1, 2, 3, 4, 5, 6]


class SampleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Sample
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    # id = factory.Sequence(lambda n: n)
    recipe = factory.RelatedFactory("test.database.factories.RecipeFactory", "sample")
    properties = factory.RelatedFactory(
        "test.database.factories.PropertiesFactory", "sample"
    )
    authors = factory.RelatedFactoryList(
        "test.database.factories.AuthorFactory",
        "sample",
        size=lambda: LIST_SIZES[random.randint(0, 5)],
    )
    raman_files = factory.RelatedFactoryList(
        "test.database.factories.RamanFileFactory",
        "sample",
        size=lambda: LIST_SIZES[random.randint(0, 5)],
    )
    sem_files = factory.RelatedFactoryList(
        "test.database.factories.SemFileFactory",
        "sample",
        size=lambda: LIST_SIZES[random.randint(0, 5)],
    )
    #raman_set = factory.RelatedFactory("test.database.factories.RamanSetFactory", "sample")

    nanohub_userid = factory.Faker("pyint", min_value=0, max_value=9999, step=1)
    experiment_date = factory.Faker("date")
    material_name = factory.Iterator(Sample.material_name.info["choices"])
    validated = factory.Faker("boolean", chance_of_getting_true=50)
