""" Tests for the Recipe model

Test relationships, properties and delete cascade behavior.

Conventions:

  test naming:
    test_rel__arelationship: 
    test_prop__aproperty:
    

"""
from math import isclose

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

    def test_prop__average_carbon_flow_rate(self, sample, all_sample_query):
        for r, s in zip(all_sample_query, sample):
            for p in r.recipe.preparation_steps:
                print(f"{p.carbon_source_flow_rate}")
            print(
                f"average: {r.recipe.average_carbon_flow_rate}"
                f"average: {s.recipe.average_carbon_flow_rate}"
            )
        assert all(
            [isclose(r.recipe.average_carbon_flow_rate, s.recipe.average_carbon_flow_rate) 
             for r, s in zip(all_sample_query, sample)]
        )

    def test_prop__average_carbon_flow_rate_query(self, sample, all_sample_query):
        sesh = dal.Session()
        query = sesh.query(Recipe.average_carbon_flow_rate).all()
        for r in query:
            print(r)


    def test_prop__carbon_source(self, sample, all_sample_query):
        for r in all_sample_query:
            for p in r.recipe.preparation_steps:
                print(f"step: {p.carbon_source}")
            print(f"recipe: {r.recipe.carbon_source}")

    def test_prop__carbon_source_query(self, sample, all_sample_query):
        sesh = dal.Session()
        query = sesh.query(Recipe.carbon_source).all()
        for r in query:
            print(r)
    
    def test_prop__uses_helium(self, sample, all_sample_query):
        for r in all_sample_query:
            print(f"recipe uses helium: {r.recipe.uses_helium}")
            for p in r.recipe.preparation_steps:
                print(f"{p.helium_flow_rate}")

    def test_prop__uses_helium_query(self, sample, all_sample_query):
        sesh = dal.Session()
        query = sesh.query(Recipe.uses_helium).all()
        for r in query:
            print(r)

    def test_prop__uses_argon(self, sample, all_sample_query):
        for r in all_sample_query:
            print(f"recipe uses argon: {r.recipe.uses_argon}")
            for p in r.recipe.preparation_steps:
                print(f"{p.argon_flow_rate}")

    def test_prop__uses_argon_query(self, sample, all_sample_query):
        sesh = dal.Session()
        query = sesh.query(Recipe.uses_argon).all()
        for r in query:
            print(r)

    def test_prop__uses_hydrogen(self, sample, all_sample_query):
        for r in all_sample_query:
            print(f"recipe uses hydrogen: {r.recipe.uses_hydrogen}")
            for p in r.recipe.preparation_steps:
                print(f"{p.hydrogen_flow_rate}")

    def test_prop__uses_hydrogen_query(self, sample, all_sample_query):
        sesh = dal.Session()
        query = sesh.query(Recipe.uses_hydrogen).all()
        for r in query:
            print(r)

    def test__json_encodable(self, sample, all_sample_query):
        for r in all_sample_query:
            print(r.recipe.json_encodable())
        
