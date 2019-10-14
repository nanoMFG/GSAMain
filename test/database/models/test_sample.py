""" Tests for the Sample model

Test relationships, properties and delete cascade behavior.

Conventions:

  test naming:
    test_rel__arelationship: 
    test_prop__aproperty:
    

"""

from gresq.database import dal
from gresq.database.models import Sample

class TestSampleQueries:
    def test_simple(self, sample, all_sample_query):
        for row in all_sample_query:
            print(f"row: {row.id}, {row.nanohub_userid}, {row.material_name}, {row.experiment_date}")

    def test_rel__recipe(self, sample, all_sample_query):
        for r in all_sample_query:
            print(
                (f"{r.recipe.id}, {r.recipe.sample_id}, "
                f"{r.recipe.thickness}, {r.recipe.diameter}, {r.recipe.length}, "
                f"{r.recipe.catalyst}, {r.recipe.tube_diameter}, {r.recipe.cross_sectional_area}, "
                f"{r.recipe.tube_length}, {r.recipe.base_pressure}, {r.recipe.dewpoint}, "
                f"{r.recipe.sample_surface_area}"
                )
                )
        assert all([s.id == r.recipe.sample_id for r, s in zip(all_sample_query, sample)])

    def test_rel__authors(self, sample, all_sample_query):
        pass

    def test_rel__raman_files(self, sample, all_sample_query):
        for r in all_sample_query:
            for f in r.raman_files:
                print(f"{f.filename}, {f.url}, {f.wavelength}")
    
    def test_rel__sem_files(self, sample, all_sample_query):
        for r in all_sample_query:
            for f in r.sem_files:
                print(f"{f.id}, {f.sample_id}, {f.filename}, {f.url}")

    def test_rel__properties(self, sample, all_sample_query):
        for r in all_sample_query:
            print(f"{r.properties.id}, {r.properties.sample_id}, \
            {r.properties.average_thickness_of_growth}, \
            {r.properties.shape}")

        assert all(
                [s.properties.id == r.properties.id for r, s in zip(all_sample_query, sample)]
                )
        assert all(
                [s.id == r.properties.sample_id for r, s in zip(all_sample_query, sample)]
                )

    def test_prop__author_last_names(self, sample, all_sample_query):
        for r, s in zip(all_sample_query, sample):
            print(r.author_last_names)
        assert all (
            [s.author_last_names == r.author_last_names for r, s in zip(all_sample_query, sample)]
        )

    

    def test__json_encodable(self, sample, all_sample_query):
        for r in all_sample_query:
            print(r.json_encodable())



class TestSampleDelete:
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

            
