from gresq.database import sample, preparation_step, recipe, properties
#from gresq.config import config
#from gresq.recipe import Recipe
from sqlalchemy import String, Integer, Float, Numeric
import pandas as pd
import os
sql_validator = {
    'int': lambda x: isinstance(x.property.columns[0].type,Integer),
    'float': lambda x: isinstance(x.property.columns[0].type,Float),
    'str': lambda x: isinstance(x.property.columns[0].type,String)
}
def convert(value,field):
    if sql_validator['int'](field):
        return int(value)
    elif sql_validator['float'](field):
        return float(value)
    else:
        return str(value)

sample_fields = [
    "material_name",
    "experiment_date"
]

preparation_fields = [
    'name',
    'duration',
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
        s.validated = True
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
                    value = convert(data.iloc[i,j],getattr(properties,dbkey))
                    # print('properties',dbkey,value,type(value))
                    setattr(pr,dbkey,value)
                elif dbkey in recipe_fields:
                    value = convert(data.iloc[i,j],getattr(recipe,dbkey))
                    # print('recipe',dbkey,value,type(value))
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
                dbkey = var_map[col_names[j+p]][0]
                value = data.iloc[i,j+p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(data.iloc[i,j+p],getattr(preparation_step,dbkey))
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if 'flow_rate' in dbkey:
                        if 'sccm' in col_names[j+p]:
                            setattr(prep,dbkey,value)
                        else:
                            setattr(prep,dbkey,value/0.01270903)
                    elif 'furnace_pressure' in dbkey:
                        setattr(prep,dbkey,value*1e3)
                    else:
                        setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Annealing')
                # print(vars(prep))
                session.add(prep)
                session.commit()
        # Growing
        for step,j in enumerate(range(110,188,13)):
            prep = preparation_step()
            prep.name = "Growing"
            prep.recipe_id = r.id
            for p in range(13):
                dbkey = var_map[col_names[j+p]][0]
                value = data.iloc[i,j+p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(data.iloc[i,j+p],getattr(preparation_step,dbkey))
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if 'flow_rate' in dbkey:
                        if 'sccm' in col_names[j+p]:
                            setattr(prep,dbkey,value)
                        else:
                            setattr(prep,dbkey,value/0.01270903)
                    elif 'furnace_pressure' in dbkey:
                        setattr(prep,dbkey,value*1e3)
                    else:
                        setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Growing')
                # print(vars(prep))
                session.add(prep)
                session.commit()
        # Cooling
        for step,j in enumerate(range(191,268,13)):
            prep = preparation_step()
            prep.name = "Cooling"
            prep.cooling_rate = convert(data.iloc[i,190],getattr(preparation_step,'cooling_rate'))
            prep.recipe_id = r.id
            for p in range(13):
                dbkey = var_map[col_names[j+p]][0]
                value = data.iloc[i,j+p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(data.iloc[i,j+p],getattr(preparation_step,dbkey))
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if 'flow_rate' in dbkey:
                        if 'sccm' in col_names[j+p]:
                            setattr(prep,dbkey,value)
                        else:
                            setattr(prep,dbkey,value/0.01270903)
                    elif 'furnace_pressure' in dbkey:
                        setattr(prep,dbkey,value*1e3)
                    else:
                        setattr(prep,dbkey,value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Cooling')
                # print(vars(prep))
                session.add(prep)
                session.commit()
        session.commit()
