from gresq.database import sample, preparation_step, dal, Base, recipe, properties, mdf_forge
from gresq.config import config
from gresq.recipe import Recipe
import pandas as pd
import os

sample_fields = [
    "material_name",
    "experiment_date"
]

preparation_fields = [
    'name',
    'timestamp',
    'furnace_temperature',
    'furnace_pressure',
    'sample_location',
    'helium_flow_rate',
    'hydrogen_flow_rate',
    'argon_flow_rate',
    'carbon_source',
    'carbon_source_flow_rate',
    'cooling_rate'
]

recipe_fields = [
    "catalyst",
    "tube_diameter",
    "cross_sectional_area",
    "tube_length",
    "base_pressure",
    "thickness",
    "diameter",
    "length"
]

properties_fields = [
    "average_thickness_of_growth",
    "standard_deviation_of_growth",
    "number_of_layers",
    "growth_coverage",
    "domain_size",
    "shape"
]
all_fields = sample_fields+preparation_fields+recipe_fields+properties_fields
def build_db(session,filepath):
    var_map = pd.read_csv(os.path.join(filepath,'varmap2.csv')).to_dict()
    data = pd.read_csv(os.path.join(filepath,'recipe_2018_11_08.csv')).iloc[:-1,:]

    col_names = data.columns
    for i in range(data.shape[0]):
        s = sample()
        s.material_name = "Graphene"
        session.add(s)
        session.commit()

        pr = properties()
        pr.sample_id = s.id
        r = recipe()
        r.sample_id = s.id
        for j in range(30):
            value = data.iloc[i,j]
            if pd.isnull(value) == False:
                dbkey = var_map[col_names[j]][0]
                if dbkey in properties_fields:
                    setattr(pr,dbkey,value)
                elif dbkey in recipe_fields:
                    setattr(r,dbkey,value)
        session.add(pr)
        session.add(r)
        session.commit()

        total_steps = 0
        # Annealing
        for step,j in enumerate(range(31,109,13)):
            prep = preparation_step()
            prep.name = "Annealing"
            prep.recipe_id = r.id
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
                    setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                session.add(prep)
        # Growing
        for step,j in enumerate(range(109,188,13)):
            prep = preparation_step()
            prep.name = "Growing"
            prep.recipe_id = r.id
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
                    setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                session.add(prep)
        # Cooling
        for step,j in enumerate(range(190,268,13)):
            prep = preparation_step()
            prep.name = "Cooling"
            prep.cooling_rate = data.iloc[i,190]
            prep.recipe_id = r.id
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
                    setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                session.add(prep)
        session.commit()

        mdf_recipe = Recipe(s.json_encodable())
        mdf = mdf_forge()
        mdf.mdf_id = s.id
        mdf.catalyst = mdf_recipe.catalyst
        mdf.max_temperature = mdf_recipe.max_temp()
        mdf.carbon_source = mdf_recipe.carbon_source()
        mdf.base_pressure = mdf_recipe.base_pressure
        session.add(mdf)
        session.commit()
