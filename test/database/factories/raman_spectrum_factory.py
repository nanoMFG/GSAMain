import factory

from gresq.database.models import RamanSpectrum
from gresq.database.dal import dal

LIST_SIZES = [1, 2, 3, 4, 5, 6]


class RamanSpectrumFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = RamanSpectrum
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    raman_file = factory.SubFactory(
        "test.database.factories.RamanFileFactory", raman_spectrum=None
    )
    xcoord = factory.Faker("pyint", min_value=0, max_value=100)
    ycoord = factory.Faker("pyint", min_value=0, max_value=100)
    percent = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=100.0)
    d_peak_shift = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    d_peak_amplitude = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    d_fwhm = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=100.0)
    g_peak_shift = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    g_peak_amplitude = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    g_fwhm = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=100.0)
    g_prime_peak_shift = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    g_prime_peak_amplitude = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    g_prime_fwhm = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
