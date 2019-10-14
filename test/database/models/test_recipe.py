""" Tests for the Recipe model

Test relationships, properties and delete cascade behavior.

Conventions:

  test naming:
    test_rel__arelationship: 
    test_prop__aproperty:
    

"""

#from gresq.database import dal
#from gresq.database.models import Sample, Recipe

class TestQueries:
    def test_simple(self, sample, all_sample_query):
        pass

    def test_rel__preparation_steps(self, sample, all_sample_query):
        pass

    def test_prop__maximum_temperature(self, sample, all_sample_query):
        for r in all_sample_query:
            print(
                f"{r.recipe.maximum_temperature}"
            )
        assert all(
            [r.recipe.maximum_temperature == s.recipe.maximum_temperature 
             for r, s in zip(all_sample_query, sample)]
        )
