from gresq.database import sample, preparation_step, dal, Base
from gresq.config import config
import pandas as pd
import os

def build_db(session,filepath):
    var_map = pd.read_csv(os.path.join(filepath,'varmap.csv')).to_dict()
    data = pd.read_csv(os.path.join(filepath,'recipestest.csv')).iloc[:-1,:]

    col_names = data.columns
    for i in range(data.shape[0]):
        s = sample()
        s.reference = data.iloc[i,-1]
        for j in range(31):
            value = data.iloc[i,j]
            if pd.isnull(value) == False:
                dbkey = var_map[col_names[j]][0]
                setattr(s,dbkey,value)
        session.add(s)
        session.commit()
        # Annealing
        for step,j in enumerate(range(32,110,13)):
            prep = preparation_step()
            prep.name = "Annealing"
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
        #                     print(dbkey,value)
                    setattr(prep,dbkey,value)
            session.add(prep)
        # Growing
        for step,j in enumerate(range(110,189,13)):
            prep = preparation_step()
            prep.name = "Growing"
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
        #                     print(dbkey,value)
                    setattr(prep,dbkey,value)
            session.add(prep)
        # Cooling
        for step,j in enumerate(range(191,269,13)):
            prep = preparation_step()
            prep.name = "Cooling"
            prep.cooling_rate = data.iloc[i,190]
            prep.sample_id = s.id
            prep.step = step
            for p in range(13):
                value = data.iloc[i,j+p]
                dbkey = var_map[col_names[j+p]][0]
                if pd.isnull(value) == False:
        #                     print(dbkey,value)
                    setattr(prep,dbkey,value)
            session.add(prep)
        session.commit()