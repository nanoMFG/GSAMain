import factory
import random

from gresq.database.models import RamanSet
from gresq.database.dal import dal

LIST_SIZES = [1, 2, 3, 4, 5, 6]


class RamanSetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = RamanSet
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    #sample = factory.SubFactory("test.database.factories.SampleFactory", raman_set=None)
    #raman_spectra = factory.SubFactory("test.database.factories.RamanSpectrumFactory", raman_set=None)
    # setauthors = factory.RelatedFactoryList(
    #     "test.database.factories.AuthorFactory",
    #     "raman_set",
    #     size=lambda: LIST_SIZES[random.randint(0, 5)],
    # )