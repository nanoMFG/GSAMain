import factory

from gresq.database.models import Author
from gresq.database.dal import dal


class AuthorFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Author
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", authors=None)
    #raman_set = factory.SubFactory("test.database.factories.RamanSetFactory", setauthors=None)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    institution = "University of Illinois"
