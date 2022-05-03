import factory

from grdb.database.v1_1_0.models import SemFile
from grdb.database.v1_1_0.dal import dal

LIST_SIZES = [1, 2, 3]


class SemFileFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = SemFile
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", sem_files=None)
    analyses = factory.RelatedFactoryList(
        "test.database.factories.SemAnalysisFactory", "sem_file", size=3
    )

    filename = factory.Faker("file_name", extension="tif")
    url = factory.Faker("url")
