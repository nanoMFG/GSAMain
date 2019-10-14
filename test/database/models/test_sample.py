""" Tests for the Sample model

Test relationships, properties and delete cascade behavior.

Conventions:

  test naming:
    test_rel__arelationship: 
    test_prop__aproperty:
    

"""
import pytest

from gresq.config import Config
from gresq.database import dal, Base
from gresq.database.models import Sample, Recipe
from ..factories import SampleFactory, RecipeFactory
from .. import config_prefix, config_suffix

@pytest.fixture(scope="class")
def sample():
    """Set up a set of samples for testing using the factory boy factories.
    The sample factory cascades to all related tables. 
    """
    # create_all is already in test/database__init__.py. 
    #  I don't know why I have to call it here again, but I do.
    Base.metadata.create_all(bind=dal.engine)
    # Add some data here
    print("Hey, here come some samples...")
    yield SampleFactory.create_batch(5)
    # Drop and ditch
    print("Tearing down test samples and DB")
    with dal.session_scope(autocommit=True) as sess:
        for s in sess.query(Sample).all():
            sess.delete(s)
    Base.metadata.drop_all(bind=dal.engine)

@pytest.fixture
def sesh():
    print("new sesh")
    s = dal.Session()
    yield s
    #print("remove sesh")
    #s.close()

@pytest.fixture(scope="class")
def query():
    """Provide a query with all current samples
    
    Returns:
        Query: All samples
    """
    sesh =  dal.Session()
    return sesh.query(Sample).all()

class TestQueries:
    def test_simple(self, sample, query):
        for row in query:
            print(f"row: {row.id}, {row.nanohub_userid}, {row.material_name}, {row.experiment_date}")

    def test_rel__recipe(self, sample, query):
        for r, s in zip(query, sample):
            print(f"{s.recipe.id}, {r.recipe.id}, {s.id}, {r.recipe.sample_id}")
            assert s.recipe.id == r.recipe.id
            assert s.id == r.recipe.sample_id

    def test_rel__raman_files(self, sample, query):
        for r in query:
            for f in r.raman_files:
                print(f"{f.filename}, {f.url}, {f.wavelength}")

    def test_rel__properties(self, sample, query):
        for r in query:
            print(f"{r.properties.id}, {r.properties.sample_id}, \
            {r.properties.average_thickness_of_growth}, \
            {r.properties.shape}")

        assert all(
                [s.properties.id == r.properties.id for r, s in zip(query, sample)]
                )
        assert all(
                [s.id == r.properties.sample_id for r, s in zip(query, sample)]
                )

    def test_prop__author_last_names(self, sample, query):
        for r, s in zip(query, sample):
            print(r.author_last_names)
        assert all (
            [s.author_last_names == r.author_last_names for r, s in zip(query, sample)]
        )

    def test__json_encodable(self, sample, query):
        for r in query:
            print(r.json_encodable())



class TestDelete:
    def test_delete_a_sample(self, sample):
        return 1
        
    def test_delete__1stsample_cascade(self, sample):
        with dal.session_scope(autocommit=True) as sess:
            smpl = sess.query(Sample).filter(Sample.id==1).one()
            assert smpl.id == 1
            sess.delete(smpl)
            print(sess.query(Sample.id).all()[0][0])
        # Check id not in sess
        # check id not in recipe
        #...



# class TestRecipe:
#     def test_recipe(self, sample):
#        n = len(sample)
#        assert sample[n-1].id == sample[n-1].recipe.sample.id
#        with dal.session_scope() as sess:
#             row = sess.query(Sample).all()[0]
#             sess.delete(row)
#             sess.commit()
            
