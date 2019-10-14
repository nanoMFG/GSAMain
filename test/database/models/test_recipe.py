""" Tests for the Recipe model

Test relationships, properties and delete cascade behavior.

Conventions:

  test naming:
    test_rel__arelationship: 
    test_prop__aproperty:
    

"""

from gresq.database import dal
from gresq.database.models import Sample, Recipe

class TestRecipeQueries:
    def test_simple(self, sample, all_sample_query):
        pass

    def test_rel__preparation_steps(self, sample, all_sample_query):
        pass

    def test_prop__maximum_temperature(self, sample, all_sample_query):
        for r in all_sample_query:
            for p in r.recipe.preparation_steps:
                print(f"{p.furnace_temperature}")
            print(
                f"max: {r.recipe.maximum_temperature}"
            )
        assert all(
            [r.recipe.maximum_temperature == s.recipe.maximum_temperature 
             for r, s in zip(all_sample_query, sample)]
        )

    def test_prop__maximum_temperature_query(self, sample):
        sesh = dal.Session()
        query = sesh.query(Recipe.maximum_temperature).all()
        for r in query:
            print(r)
        assert False

    def test_prop__maximum_pressure(self, sample, all_sample_query):
        for r in all_sample_query:
            for p in r.recipe.preparation_steps:
                print(f"{p.furnace_pressure}")
            print(
                f"max: {r.recipe.maximum_pressure}"
            )
        assert all(
            [r.recipe.maximum_pressure == s.recipe.maximum_pressure 
             for r, s in zip(all_sample_query, sample)]
        )

    def test_prop__maximum_pressure_query(self, sample):
        sesh = dal.Session()
        query = sesh.query(Recipe.maximum_pressure).all()
        for r in query:
            print(r)

        assert False