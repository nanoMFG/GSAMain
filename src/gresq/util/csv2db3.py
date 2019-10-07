from gresq.database import sample, preparation_step, dal, Base, recipe, properties, mdf_forge, raman_set, raman_file, raman_spectrum, sem_file, author
from gresq.config import config
from gresq.recipe import Recipe
from sqlalchemy import String, Integer, Float, Numeric
from gresq.util.box_adaptor import BoxAdaptor
import uuid
import pandas as pd
import os
import sys
import datetime
from datetime import date
par = os.path.abspath(os.path.pardir)
sys.path.append(os.path.join(par,'src','gresq','dashboard', 'gsaraman','src'))
from gsaraman.gsaraman import auto_fitting
sample_key = {
    'experiment_date': 'DATE'
}
properties_key = {
    'average_thickness_of_growth':'PROPERTY: Average Thickness of Growth (nm)',
    'standard_deviation_of_growth':'PROPERTY: Standard Deviation of Growth (nm)',
    'number_of_layers': 'PROPERTY: Number of Layers',
    'growth_coverage': 'PROPERTY: Growth Coverage (%)',
    }
recipe_key = {
    'sample_surface_area':'PROPERTY: Sample Surface Area (mm$\^2$)',
    'thickness': 'PROPERTY: Thickness ($\mu$m)',
    'tube_diameter': 'ALL CONDITION: Tube Diameter (mm)',
    'tube_length': 'ALL CONDITION: Tube Length (mm)',
    'catalyst': 'ALL CONDITION: Catalyst',
    'cross_sectional_area': 'ALL CONDITION: Cross Sectional Area (mm^2)',
    'base_pressure': 'ALL CONDITION: Base Pressure (mTorr)',
}
preparation_step_key = {
    'duration': 'PREPARATION STEP DETAIL: Timestamp',
    'furnace_temperature': 'PREPARATION STEP DETAIL: Furnace Temperature',
    'furnace_pressure': 'PREPARATION STEP DETAIL: Furnace Pressure',
    'sample_location': 'PREPARATION STEP DETAIL: Sample Location',
    'helium_flow_rate': 'PREPARATION STEP DETAIL: Helium Flow Rate', ## l/s vs sccm
    'hydrogen_flow_rate': 'PREPARATION STEP DETAIL: Hydrogen Flow Rate',
    'carbon_source': 'PREPARATION STEP DETAIL: Carbon Source',
    'carbon_source_flow_rate': 'PREPARATION STEP DETAIL: Carbon Source Flow Rate',
    'argon_flow_rate': 'PREPARATION STEP DETAIL: Argon Flow Rate'
}

sql_validator = {
    'int': lambda x: isinstance(x.property.columns[0].type,Integer),
    'float': lambda x: isinstance(x.property.columns[0].type,Float),
    'str': lambda x: isinstance(x.property.columns[0].type,String)
}
def convert(value,field,header=None):
    if sql_validator['int'](field):
        return int(value)
    elif sql_validator['float'](field):
        value = float(value)
        if 'mTorr' in header:
            value /= 1000
        return value
    else:
        return str(value)

def upload_file(file_path,folder_name=None):
    box_config_path='/Users/Joshua_Schiller/Dropbox/GSAMain/src/box_config.json'
    box_adaptor = BoxAdaptor(box_config_path)
    upload_folder = box_adaptor.create_upload_folder(folder_name=folder_name)
    box_file = box_adaptor.upload_file(upload_folder,file_path,str(uuid.uuid4()))

    return box_file.get_shared_link_download_url(access='open')

def get_filepaths(reference_id,folder_path = './'):
    contents = os.listdir(os.path.join(folder_path,reference_id))
    raman = []
    sem = []
    for f in contents:
        if f.split('.')[-1]=='txt':
            raman.append(f)
        elif f.split('.')[-1]=='tif':
            sem.append(f)
    return raman, sem

def convert_date(d):
    words = d.split('/')
    month = int(words[0])
    day = int(words[1])
    year = int('20'+words[2])
    return date(year,month,day)

def convert_db(data):
    columns = data.columns
    for i in range(data.shape[0]):
        for c,col in enumerate(columns):
            if 'Torr l/s' in col:
                value = data[col][i]
                if pd.isnull(value) == False:
                    value = float(value)
                    new_col = col.replace('Torr l/s','sccm')
                    if pd.isnull(data[new_col][i]):
                        data[new_col][i] = value/0.01270903
    new_cols = [col for col in columns if 'Torr l/s' not in col]
    data = data[new_cols].copy()

    return data


def build_db(session,filepath,sem_raman_path=None):
    data = pd.read_csv(os.path.join(filepath,'recipe_2019-08-27.csv'))
    data = convert_db(data)

    name_idxs = []
    cooling_idx = None
    for c, col in enumerate(data.columns):
        if 'PREPARATION STEP NAME' in col:
            name_idxs.append(c)
        elif 'Cooling Rate' in col:
            cooling_idx = c

    annealing_df = data.iloc[:,name_idxs[0]+1:name_idxs[1]].copy()
    growing_df = data.iloc[:,name_idxs[1]+1:name_idxs[2]].copy()
    cooling_df = data.iloc[:,cooling_idx+1:].copy()
    cooling_rate = data.iloc[:,cooling_idx].copy()
    box_folder = data['BOX FOLDER'].copy()
    author_column = data['CONTRIBUTOR'].copy()

    for i in range(data.shape[0]):
        if 'Kaihao' in author_column[i]:
            s = sample()
            s.material_name = "Graphene"
            s.validated = True
            date_string = data[sample_key['experiment_date']][i]
            if pd.isnull(date_string)==False:
                s.experiment_date = convert_date(date_string)

            session.add(s)
            session.flush()

            pr = properties()
            pr.sample_id = s.id
            for key,header in properties_key.items():
                value = data[header][i]
                if pd.isnull(value) == False:
                    value = convert(value,getattr(properties,key),header=header)
                    setattr(pr,key,value)

            r = recipe()
            r.sample_id = s.id
            for key,header in recipe_key.items():
                value = data[header][i]
                if pd.isnull(value) == False:
                    value = convert(value,getattr(recipe,key),header=header)
                    setattr(r,key,value)
            session.add(pr)
            session.add(r)
            session.commit()

            total_steps = 0

            for j in range(0,annealing_df.shape[1],9):
                prep_df = annealing_df.iloc[:,j:j+9].copy()
                
                initial_cols = prep_df.columns
                for col in prep_df.columns:
                    for key,value in preparation_step_key.items():
                        if value in col and preparation_step_key['carbon_source_flow_rate'] not in col:
                            prep_df.rename(columns={col:value},inplace=True)
                        elif value in col and value == preparation_step_key['carbon_source_flow_rate']:
                            prep_df.rename(columns={col:value},inplace=True)
                prep = preparation_step()
                prep.name = 'Annealing'
                prep.recipe_id = r.id
                for key,header in preparation_step_key.items():
                    try:
                        value = prep_df[header][i]
                        if pd.isnull(value) == False:
                            value = convert(value,getattr(preparation_step,key),header=header)
                            setattr(prep,key,value)
                    except Exception as e:
                        print('###################')
                        print("%s Row %s Column %s"%(prep.name,i,j)) 
                        print("Header:  '%s'"%header)
                        print(e)
                if prep.duration != None:
                    prep.step = total_steps
                    total_steps += 1
                    session.add(prep)
                    session.commit()   

            for j in range(0,growing_df.shape[1],9):
                prep_df = growing_df.iloc[:,j:j+9].copy()

                for col in prep_df.columns:
                    for key,value in preparation_step_key.items():
                        if value in col and preparation_step_key['carbon_source_flow_rate'] not in col:
                            prep_df.rename(columns={col:value},inplace=True)
                        elif value in col and value == preparation_step_key['carbon_source_flow_rate']:
                            prep_df.rename(columns={col:value},inplace=True)
                prep = preparation_step()
                prep.name = 'Growing'
                prep.recipe_id = r.id
                for key,header in preparation_step_key.items():
                    try:
                        value = prep_df[header][i]
                        if pd.isnull(value) == False:
                            value = convert(value,getattr(preparation_step,key),header=header)
                            setattr(prep,key,value)
                    except Exception as e:
                        print('###################')
                        print("%s Row %s Column %s"%(prep.name,i,j)) 
                        print("Header:  '%s'"%header)
                        print(e)
                if prep.duration != None:
                    prep.step = total_steps
                    total_steps += 1
                    session.add(prep)
                    session.commit() 

            for j in range(0,cooling_df.shape[1],9):
                prep_df = cooling_df.iloc[:,j:j+9].copy()
                if prep_df.shape[1]<9:
                    break
                for col in prep_df.columns:
                    for key,value in preparation_step_key.items():
                        if value in col and preparation_step_key['carbon_source_flow_rate'] not in col:
                            prep_df.rename(columns={col:value},inplace=True)
                        elif value in col and value == preparation_step_key['carbon_source_flow_rate']:
                            prep_df.rename(columns={col:value},inplace=True)
                prep = preparation_step()
                prep.name = 'Cooling'
                prep.recipe_id = r.id
                cooling_value = cooling_rate[i]
                if pd.isnull(cooling_value)==False:
                    prep.cooling_rate=cooling_value

                for key,header in preparation_step_key.items():
                    try:
                        value = prep_df[header][i]
                        if pd.isnull(value) == False:
                            value = convert(value,getattr(preparation_step,key),header=header)
                            setattr(prep,key,value)
                    except Exception as e:
                        print('###################')
                        print("%s Row %s Column %s"%(prep.name,i,j)) 
                        print("Header:  '%s'"%header)
                        print(e)
                if prep.duration != None:
                    prep.step = total_steps
                    total_steps += 1
                    session.add(prep)
                    session.commit()     


            ### RAMAN IS A SEPARATE DATASET FROM SAMPLE ###
            rs = raman_set()
            rs.sample_id = s.id
            rs.experiment_date = s.experiment_date
            session.add(rs)
            session.flush()

            reference_id = str(box_folder[i])
            if os.path.isdir(os.path.join(sem_raman_path,reference_id)):
                files = os.listdir(os.path.join(sem_raman_path,reference_id))
                files_response = {'Raman Files':[],'SEM Image Files':[],'Raman Wavelength':532}
                for f in files:
                    if f.split('.')[-1] == 'txt':
                        files_response['Raman Files'].append(os.path.join(sem_raman_path,reference_id,f))
                    elif f.split('.')[-1] == 'tif':
                        files_response['SEM Image Files'].append(os.path.join(sem_raman_path,reference_id,f))

                if len(files_response['Raman Files'])>0:
                    files_response['Characteristic Percentage'] = [100/len(files_response['Raman Files'])]*len(files_response['Raman Files'])
                    for ri,ram in enumerate(files_response['Raman Files']):
                        rf = raman_file()
                        rf.filename = os.path.basename(ram)
                        rf.sample_id = s.id
                        rf.url = upload_file(ram)
                        if files_response['Raman Wavelength'] != None:
                            rf.wavelength = files_response['Raman Wavelength']
                        session.add(rf)
                        session.flush()

                        params = auto_fitting(ram)
                        r = raman_spectrum()
                        r.raman_file_id = rf.id
                        r.set_id = rs.id
                        if files_response['Characteristic Percentage'] != None:
                            r.percent = float(files_response['Characteristic Percentage'][ri]) 
                        else:
                            r.percent = 0.
                        for peak in params.keys():
                            for v in params[peak].keys():
                                key = "%s_%s"%(peak,v)
                                setattr(r,key,float(params[peak][v]))
                        session.add(r)
                        session.flush()
                    
                    rs_fields = [
                    "d_peak_shift",
                    "d_peak_amplitude",
                    "d_fwhm",
                    "g_peak_shift",
                    "g_peak_amplitude",
                    "g_fwhm",
                    "g_prime_peak_shift",
                    "g_prime_peak_amplitude",
                    "g_prime_fwhm"
                    ]
                    for field in rs_fields:
                        setattr(rs,field,sum([getattr(spect,field)*getattr(spect,'percent')/100. for spect in rs.raman_spectra]))
                    rs.d_to_g = sum([getattr(spect,'d_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
                    rs.gp_to_g = sum([getattr(spect,'g_prime_peak_amplitude')/getattr(spect,'g_peak_amplitude')*getattr(spect,'percent')/100. for spect in rs.raman_spectra])
                    session.flush()

                if len(files_response['SEM Image Files'])>0:
                    for f in files_response['SEM Image Files']:
                        sf = sem_file()
                        sf.sample_id = s.id
                        sf.filename = os.path.basename(f)
                        sf.url = upload_file(f)
                        session.add(sf)
                        session.flush()

            auth = author()
            auth.first_name = 'Kaihao'
            auth.last_name = 'Zhang'
            auth.institution = 'University of Illinois at Urbana-Champaign'

            if 'Kaihao' in author_column[i]:
                auth.sample_id = s.id
                auth.raman_id = rs.id
                session.add(auth)

            session.commit()
