import factory

from gresq.database.models import RamanFile
from gresq.database.dal import dal

from .. import test_session


LIST_SIZES = [1, 2, 3]

class RamanFileFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        model = RamanFile
        sqlalchemy_session = test_session
       # sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory("test.database.factories.SampleFactory", raman_files=None)
    raman_spectrum = factory.RelatedFactory("test.database.factories.RamanSpectrumFactory", "raman_file")

    filename = factory.Faker("file_name", extension="tif")
    url = factory.Faker("url")
    wavelength = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=800.0)