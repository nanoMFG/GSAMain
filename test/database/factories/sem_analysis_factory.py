import factory

from gresq.database.models import SemAnalysis
from gresq.database.dal import dal

LIST_SIZES = [1, 2, 3]

class SemAnalysisFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = SemAnalysis
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sem_file = factory.SubFactory("test.database.factories.SemFileFactory", analyses=None)