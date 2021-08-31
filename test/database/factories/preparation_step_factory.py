import factory

from grdb.database.v1_1_0.models import PreparationStep
from grdb.database.v1_1_0.dal import dal

LIST_SIZES = [1, 2, 3]


class PreparationStepFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = PreparationStep
        sqlalchemy_session = dal.Session()
        sqlalchemy_session_persistence = "commit"

    recipe = factory.SubFactory(
        "test.database.factories.RecipeFactory", preparation_steps=None
    )

    step = factory.Iterator(LIST_SIZES)
    name = factory.Iterator(PreparationStep.name.info["choices"])
    duration = factory.Faker("pyfloat", positive=True, min_value=0.0, max_value=100.0)
    furnace_temperature = factory.Faker(
        "pyfloat", positive=True, min_value=800.0, max_value=2000.0
    )
    furnace_pressure = factory.Faker(
        "pyfloat", positive=True, min_value=80.0, max_value=100.0
    )
    sample_location = factory.Faker(
        "pyfloat", positive=True, min_value=1.0, max_value=10.0
    )
    helium_flow_rate = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    hydrogen_flow_rate = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    carbon_source = factory.Iterator(PreparationStep.carbon_source.info["choices"])
    carbon_source_flow_rate = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    argon_flow_rate = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
    cooling_rate = factory.Faker(
        "pyfloat", positive=True, min_value=0.0, max_value=100.0
    )
