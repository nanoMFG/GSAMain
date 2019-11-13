from gresq.database import (
    sample,
    preparation_step,
    dal,
    Base,
    recipe,
    properties,
    mdf_forge,
    raman_set,
    raman_file,
    raman_spectrum,
    sem_file,
)
from gresq.config import config
from gresq.recipe import Recipe
from sqlalchemy import String, Integer, Float, Numeric
import pandas as pd
import os

sql_validator = {
    "int": lambda x: isinstance(x.property.columns[0].type, Integer),
    "float": lambda x: isinstance(x.property.columns[0].type, Float),
    "str": lambda x: isinstance(x.property.columns[0].type, String),
}


def convert(value, field):
    if sql_validator["int"](field):
        return int(value)
    elif sql_validator["float"](field):
        return float(value)
    else:
        return str(value)


def upload_file(file_path, folder_name=None):
    box_adaptor = BoxAdaptor(box_config_path)
    upload_folder = box_adaptor.create_upload_folder(folder_name=folder_name)
    box_file = box_adaptor.upload_file(upload_folder, file_path, str(uuid.uuid4()))

    return box_file.get_shared_link_download_url(access="open")


def get_filepaths(reference_id, folder_path="./"):
    contents = os.listdir(os.path.join(folder_path, reference_id))
    raman = []
    sem = []
    for f in contents:
        if f.split(".")[-1] == "txt":
            raman.append(f)
        elif f.split(".")[-1] == "tif":
            sem.append(f)
    return raman, sem


sample_fields = ["material_name", "experiment_date"]

preparation_fields = [
    "name",
    "duration",
    "furnace_temperature",
    "furnace_pressure",
    "sample_location",
    "helium_flow_rate",
    "hydrogen_flow_rate",
    "argon_flow_rate",
    "carbon_source",
    "carbon_source_flow_rate",
    "cooling_rate",
]

recipe_fields = [
    "catalyst",
    "tube_diameter",
    "cross_sectional_area",
    "tube_length",
    "base_pressure",
    "thickness",
    "diameter",
    "length",
]

properties_fields = [
    "average_thickness_of_growth",
    "standard_deviation_of_growth",
    "number_of_layers",
    "growth_coverage",
    "domain_size",
    "shape",
]
all_fields = sample_fields + preparation_fields + recipe_fields + properties_fields


def build_db(session, filepath, sem_raman_path=None):
    var_map = pd.read_csv(os.path.join(filepath, "varmap2.csv")).to_dict()
    data = pd.read_csv(os.path.join(filepath, "recipe_2018_11_08.csv")).iloc[:-1, :]

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
            value = data.iloc[i, j]
            if pd.isnull(value) == False:
                dbkey = var_map[col_names[j]][0]
                if dbkey == "identifier":
                    identifier = str(data.iloc[i, j])
                if dbkey in properties_fields:
                    value = convert(data.iloc[i, j], getattr(properties, dbkey))
                    setattr(pr, dbkey, value)
                elif dbkey in recipe_fields:
                    value = convert(data.iloc[i, j], getattr(recipe, dbkey))
                    if "mTorr" in col_names[j]:
                        setattr(prep, dbkey, value / 1000)
                    else:
                        setattr(prep, dbkey, value)
        session.add(pr)
        session.add(r)
        session.commit()

        total_steps = 0
        # Annealing
        for step, j in enumerate(range(31, 109, 13)):
            prep = preparation_step()
            prep.name = "Annealing"
            prep.recipe_id = r.id
            for p in range(13):
                dbkey = var_map[col_names[j + p]][0]
                value = data.iloc[i, j + p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(
                        data.iloc[i, j + p], getattr(preparation_step, dbkey)
                    )
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if "flow_rate" in dbkey:
                        if "sccm" in col_names[j + p]:
                            setattr(prep, dbkey, value)
                        else:
                            setattr(prep, dbkey, value / 0.01270903)
                    elif "furnace_pressure" in dbkey:
                        if "mTorr" in col_names[j + p]:
                            setattr(prep, dbkey, value / 1000)
                        else:
                            setattr(prep, dbkey, value)
                    else:
                        setattr(prep, dbkey, value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Annealing')
                # print(vars(prep))
                session.add(prep)
                session.commit()
        # Growing
        for step, j in enumerate(range(110, 188, 13)):
            prep = preparation_step()
            prep.name = "Growing"
            prep.recipe_id = r.id
            for p in range(13):
                dbkey = var_map[col_names[j + p]][0]
                value = data.iloc[i, j + p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(
                        data.iloc[i, j + p], getattr(preparation_step, dbkey)
                    )
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if "flow_rate" in dbkey:
                        if "sccm" in col_names[j + p]:
                            setattr(prep, dbkey, value)
                        else:
                            setattr(prep, dbkey, value / 0.01270903)
                    elif "furnace_pressure" in dbkey:
                        if "mTorr" in col_names[j + p]:
                            setattr(prep, dbkey, value / 1000)
                        else:
                            setattr(prep, dbkey, value)
                    else:
                        setattr(prep, dbkey, value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Growing')
                # print(vars(prep))
                session.add(prep)
                session.commit()
        # Cooling
        for step, j in enumerate(range(191, 268, 13)):
            prep = preparation_step()
            prep.name = "Cooling"
            prep.cooling_rate = convert(
                data.iloc[i, 190], getattr(preparation_step, "cooling_rate")
            )
            prep.recipe_id = r.id
            for p in range(13):
                dbkey = var_map[col_names[j + p]][0]
                value = data.iloc[i, j + p]
                if pd.isnull(value) == False and dbkey in preparation_fields:
                    value = convert(
                        data.iloc[i, j + p], getattr(preparation_step, dbkey)
                    )
                    # print(prep.name,col_names[j+p],dbkey,value,type(value))
                    if "flow_rate" in dbkey:
                        if "sccm" in col_names[j + p]:
                            setattr(prep, dbkey, value)
                        else:
                            setattr(prep, dbkey, value / 0.01270903)
                    elif "furnace_pressure" in dbkey:
                        if "mTorr" in col_names[j + p]:
                            setattr(prep, dbkey, value / 1000)
                        else:
                            setattr(prep, dbkey, value)
                    else:
                        setattr(prep, dbkey, value)
            if prep.duration != None:
                prep.step = total_steps
                total_steps += 1
                # print('Added Cooling')
                # print(vars(prep))
                session.add(prep)
                session.commit()

        ### RAMAN IS A SEPARATE DATASET FROM SAMPLE ###
        rs = raman_set()
        rs.sample_id = s.id
        # rs.experiment_date = provenance_response['sample']['experiment_date']['value']
        session.add(rs)
        session.flush()

        files = os.listdir(os.path.join(sem_raman_path, identifier))
        files_response = {"Raman Files": [], "SEM Image Files": []}
        for f in files:
            if f.split(".")[-1] == "txt":
                files_response["Raman Files"].append(
                    os.path.join(sem_raman_path, identifier, f)
                )
            elif f.split(".")[-1] == "tif":
                files_response["SEM Image Files"].append(
                    os.path.join(sem_raman_path, identifier, f)
                )

        files_response["Characteristic Percentage"] = [
            1 / len(files_response["Raman Files"])
        ] * len(files_response["Raman Files"])

        for ri, ram in enumerate(files_response["Raman Files"]):
            rf = raman_file()
            rf.filename = os.path.basename(ram)
            rf.sample_id = s.id
            rf.url = upload_file(ram)
            if files_response["Raman Wavength"] != None:
                rf.wavelength = files_response["Raman Wavength"]
            session.add(rf)
            session.flush()

            params = GSARaman.auto_fitting(ram)
            r = raman_spectrum()
            r.raman_file_id = rf.id
            r.set_id = rs.id
            if files_response["Characteristic Percentage"] != None:
                r.percent = float(files_response["Characteristic Percentage"][ri])
            else:
                r.percent = 0.0
            for peak in params.keys():
                for v in params[peak].keys():
                    key = "%s_%s" % (peak, v)
                    setattr(r, key, float(params[peak][v]))
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
            "g_prime_fwhm",
        ]
        for field in rs_fields:
            setattr(
                rs,
                field,
                sum(
                    [
                        getattr(spect, field) * getattr(spect, "percent") / 100.0
                        for spect in rs.raman_spectra
                    ]
                ),
            )
        rs.d_to_g = sum(
            [
                getattr(spect, "d_peak_amplitude")
                / getattr(spect, "g_peak_amplitude")
                * getattr(spect, "percent")
                / 100.0
                for spect in rs.raman_spectra
            ]
        )
        rs.gp_to_g = sum(
            [
                getattr(spect, "g_prime_peak_amplitude")
                / getattr(spect, "g_peak_amplitude")
                * getattr(spect, "percent")
                / 100.0
                for spect in rs.raman_spectra
            ]
        )
        session.flush()

        for f in files_response["SEM Image Files"]:
            sf = sem_file()
            sf.sample_id = s.id
            sf.filename = os.path.basename(f)
            sf.url = self.upload_file(f)
            session.add(sf)
            session.flush()

        session.commit()
