import pytest

from gresq.config import Config
from gresq.database import dal, Base
from gresq.database.models import Sample, Recipe
from ..factories import SampleFactory, RecipeFactory
from .. import config_prefix, config_suffix

@pytest.fixture
def sample(scope="module"):
    #conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
    #dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
   
    Base.metadata.create_all(bind=dal.engine)
    # Add some data here

    yield SampleFactory.create_batch(5)
    #with dal.session_scope(autocommit=True) as sess:
    #    for s in sess.query(Sample).all():
    #        sess.delete(s)
    # Drop and ditch
    #Base.metadata.drop_all(bind=dal.engine)
    #dal.engine.dispose()


class TestSample:
    def test_simple(self, sample):
        
        print(sample[8].id)
        with dal.session_scope() as sess:
            for row in sess.query(Sample).all():
                print(f"row: {row.id}, {row.nanohub_userid}, {row.material_name}, {row.experiment_date}")

    def test_delete__1stsample_cascade(self, sample):
        with dal.session_scope(autocommit=True) as sess:
            smpl = sess.query(Sample).filter(Sample.id==1).one()
            assert smpl.id == 1
            sess.delete(smpl)
            print(sess.query(Sample.id).all()[0][0])
        # Check id not in sess
        # check id not in recipe
        #...


class TestRecipe:
    def test_recipe(self, sample):
       n = len(sample)
       assert sample[n-1].id == sample[n-1].recipe.sample.id
       with dal.session_scope() as sess:
            row = sess.query(Sample).all()[0]
            sess.delete(row)
            sess.commit()
            
