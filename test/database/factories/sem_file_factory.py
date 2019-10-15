import factory

from gresq.database.models import SemFile
from gresq.database.dal import dal

LIST_SIZES = [1, 2, 3]

class SemFileFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = SemFile
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", sem_files=None)
    analyses = factory.RelatedFactoryList("test.database.factories.SemAnalysisFactory", 
        "sem_file", size=3)

    filename = factory.Faker("file_name", extension="tif")
    url = factory.Faker("url")