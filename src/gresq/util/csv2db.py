from gresq.database import dal, Base
from gresq.database.models import Sample, PreparationStep
from gresq.config import config
import pandas as pd
import os


def build_db(session, filepath):
    var_map = pd.read_csv(os.path.join(filepath, "varmap2.csv")).to_dict()
    data = pd.read_csv(os.path.join(filepath, "recipe_2018_11_08.csv")).iloc[:-1, :]

    col_names = data.columns
    for i in range(data.shape[0]):
        s = Sample()
        s.reference = data.iloc[i, -1]
        for j in range(30):
            value = data.iloc[i, j]
            if pd.isnull(value) == False:
                dbkey = var_map[col_names[j]][0]
                setattr(s, dbkey, value)
        session.add(s)
        session.commit()
        # Annealing
        for step, j in enumerate(range(31, 109, 13)):
            prep = PreparationStep()
            prep.name = "Annealing"
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i, j + p]
                dbkey = var_map[col_names[j + p]][0]
                if pd.isnull(value) == False:
                    #                     print(dbkey,value)
                    setattr(prep, dbkey, value)
            session.add(prep)
        # Growing
        for step, j in enumerate(range(109, 188, 13)):
            prep = PreparationStep()
            prep.name = "Growing"
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i, j + p]
                dbkey = var_map[col_names[j + p]][0]
                if pd.isnull(value) == False:
                    #                     print(dbkey,value)
                    setattr(prep, dbkey, value)
            session.add(prep)
        # Cooling
        for step, j in enumerate(range(190, 268, 13)):
            prep = PreparationStep()
            prep.name = "Cooling"
            prep.cooling_rate = data.iloc[i, 190]
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i, j + p]
                dbkey = var_map[col_names[j + p]][0]
                if pd.isnull(value) == False:
                    #                     print(dbkey,value)
                    setattr(prep, dbkey, value)
            session.add(prep)
        session.commit()
