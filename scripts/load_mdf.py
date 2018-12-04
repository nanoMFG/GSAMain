import json
import pandas as pd
import os

from gresq.database import sample, GresqEncoder
from src.gresq.database import preparation_step

"""
NAME:
    load_mdf
    
SYNOPSIS:
    Read data from the recipie CSV file and create datasets in Materials Data
    Facility.
    
DESCRIPTION:
    For now this script just reads the CSV file and generates JSON documents
    for each recipie. These documents are written to the output folder
"""
filepath = "../data"
var_map = pd.read_csv(os.path.join(filepath, 'varmap2.csv')).to_dict()
data = pd.read_csv(os.path.join(filepath, 'recipe_2018_11_08.csv')).iloc[:-1, :]

col_names = data.columns

for i in range(data.shape[0]):
    s = sample()
    s.reference = data.iloc[i, -1]
    for j in range(30):
        value = data.iloc[i, j]
        if pd.isnull(value) == False:
            dbkey = var_map[col_names[j]][0]
            setattr(s, dbkey, value)

    # Annealing
    s.annealing_steps = []
    for step,j in enumerate(range(31,109,13)):
        prep = preparation_step()
        prep.name = "Annealing"
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i,j+p]
            dbkey = var_map[col_names[j+p]][0]
            if pd.isnull(value) == False:
                setattr(prep,dbkey,value)
        s.annealing_steps.append(prep)

    # Growing
    s.growing_steps = []
    for step,j in enumerate(range(109,188,13)):
        prep = preparation_step()
        prep.name = "Growing"
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i,j+p]
            dbkey = var_map[col_names[j+p]][0]
            if pd.isnull(value) == False:
                setattr(prep,dbkey,value)
        s.growing_steps.append(prep)

    # Cooling
    s.cooling_steps = []
    for step,j in enumerate(range(190,268,13)):
        prep = preparation_step()
        prep.name = "Cooling"
        prep.cooling_rate = data.iloc[i,190]
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i,j+p]
            dbkey = var_map[col_names[j+p]][0]
            if pd.isnull(value) == False:
                setattr(prep,dbkey,value)
        s.cooling_steps.append(prep)

    with open(os.path.join("..", "output", "%s-%s.json" % (s.material_name, s.identifier)), 'w') as outfile:
        json.dump(s, outfile, cls=GresqEncoder)
