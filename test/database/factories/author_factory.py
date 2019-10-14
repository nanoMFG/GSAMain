import factory

from gresq.database.models import Author
from gresq.database.dal import dal

class AuthorFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = Author
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", author=None)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    institution = 'Uniiversity of Illinois'