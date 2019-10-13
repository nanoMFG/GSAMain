import pytest

from gresq.config import Config
from gresq.database import dal, Base
from gresq.database.models import Sample, Recipe
from ..factories import SampleFactory, RecipeFactory
from .. import config_prefix, config_suffix

@pytest.fixture(scope="class")
def sample():
    #conf = Config(prefix=config_prefix, suffix=config_suffix, debug=True, try_secrets=False)
    #dal.init_db(conf, privileges={"read": True, "write": True, "validate": True})
    print("Hey, here come some samples...")
    Base.metadata.create_all(bind=dal.engine)
    # Add some data here

    yield SampleFactory.create_batch(5)
    with dal.session_scope(autocommit=True) as sess:
        for s in sess.query(Sample).all():
            sess.delete(s)
    # Drop and ditch
    Base.metadata.drop_all(bind=dal.engine)
    #dal.engine.dispose()
@pytest.fixture
def sesh():
    print("new sesh")
    s = dal.Session()
    yield s
    #print("remove sesh")
    #s.close()

class TestSample:
    def test_simple(self, sample, sesh):
        
        #print(sample[8].id)
        #with dal.session_scope() as sess:
            for row in sesh.query(Sample).all():
                print(f"row: {row.id}, {row.nanohub_userid}, {row.material_name}, {row.experiment_date}")

    # def test_delete__1stsample_cascade(self, sample):
    #     with dal.session_scope(autocommit=True) as sess:
    #         smpl = sess.query(Sample).filter(Sample.id==1).one()
    #         assert smpl.id == 1
    #         sess.delete(smpl)
    #         print(sess.query(Sample.id).all()[0][0])
    #     # Check id not in sess
    #     # check id not in recipe
    #     #...

    def test_recipe_rel(self, sample, sesh):
        #sess = dal.Session()
        for r, s in zip(sesh.query(Sample).all(), sample):
            print(f"{s.recipe.id}, {r.recipe.id}, {s.id}, {r.recipe.sample_id}")
            assert s.recipe.id == r.recipe.id
            assert s.id == r.recipe.sample_id

    def test_properties_rel(self, sample, sesh):
        q = sesh.query(Sample).all()
        for r, s in zip(q, sample):
            print(f"{s.properties.id}, {r.properties.id}, {s.id}, {r.properties.sample_id}")

        assert all(
                [s.properties.id == r.properties.id for r, s in zip(q, sample)]
                )
        assert all(
                [s.id == r.properties.sample_id for r, s in zip(q, sample)]
                )

    def test_prop__author_last_names(self, sample, sesh):
        q = sesh.query(Sample).all()
        for r, s in zip(q, sample):
            print(r.author_last_names)
        assert all (
            [s.author_last_names == r.author_last_names for r, s in zip(q, sample)]
        )

    def test__json_encodable(self, sample, sesh):
        q = sesh.query(Sample).all()
        for r in q:
            print(r.json_encodable())

    def test_rel__raman_file(self, sample, sesh):
        q = sesh.query(Sample).all()
        for r in q:
            for f in r.raman_files:
                print(f"{f.filename}, {f.url}, {f.wavelength}")




# class TestRecipe:
#     def test_recipe(self, sample):
#        n = len(sample)
#        assert sample[n-1].id == sample[n-1].recipe.sample.id
#        with dal.session_scope() as sess:
#             row = sess.query(Sample).all()[0]
#             sess.delete(row)
#             sess.commit()
            
