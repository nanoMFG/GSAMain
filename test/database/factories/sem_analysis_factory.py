import factory

from grdb.database.v1_1_0.models import SemAnalysis
from grdb.database.v1_1_0.dal import dal

LIST_SIZES = [1, 2, 3]


class SemAnalysisFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = SemAnalysis
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sem_file = factory.SubFactory(
        "test.database.factories.SemFileFactory", analyses=None
    )

    mask_url = factory.Faker("url")
    px_per_um = factory.Faker("pyint", min_value=0, max_value=30, step=1)
    growth_coverage = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=99.0
    )
    automated = factory.Faker("boolean", chance_of_getting_true=50)
