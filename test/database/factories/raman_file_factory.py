import factory

from grdb.database.v1_1_0.models import RamanFile
from grdb.database.v1_1_0.dal import dal

LIST_SIZES = [1, 2, 3]


class RamanFileFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = RamanFile
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    sample = factory.SubFactory(
        "test.database.factories.SampleFactory", raman_files=None
    )
    raman_spectrum = factory.RelatedFactory(
        "test.database.factories.RamanSpectrumFactory", "raman_file"
    )

    filename = factory.Faker("file_name", extension="tif")
    url = factory.Faker("url")
    wavelength = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=800.0)
