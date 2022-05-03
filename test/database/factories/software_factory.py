import factory

from grdb.database.v1_1_0.models import Software
from grdb.database.v1_1_0.dal import dal


class SoftwareFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Software
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    #sample = factory.SubFactory("test.database.factories.SampleFactory", authors=None)
    #raman_set = factory.SubFactory("test.database.factories.RamanSetFactory", setauthors=None)
    name = factory.Faker("first_name")
    version = factory.Faker("last_name")
    release_date = factory.Faker("date")
    branch = 'master'
    commitsh = factory.Faker("sha1")
    url = factory.Faker("url")