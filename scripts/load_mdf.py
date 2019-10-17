import json
import os
import zipfile
from datetime import datetime

import pandas as pd
from boxsdk import DevelopmentClient
from boxsdk.object.folder import Folder
from mdf_connect_client import MDFConnectClient

from src.gresq.database import preparation_step, sample, GresqEncoder


"""
NAME:
    load_mdf
    
SYNOPSIS:
    Read data from the recipe CSV file and create datasets in Materials Data
    Facility.
    
DESCRIPTION:
    This script reads the CSV file and consults the sample_id column to 
    determine the Box folder that contains the supporting files. These files are 
    downloaded from Box into an output directory.
    
    It then generates a JSON file that represents the recipe and bundles it into
    the same output folder. This folder is then zipped up into an archive, 
    uploaded to a public staging folder in Box and a download URL is generated
    
    Finally, creates an MDF submission based on data from the CSV File record.
    
"""

class GresqEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'json_encodable'):
            return o.json_encodable()
        else:
            raise TypeError(
                'Object of type %s with value of %s is not JSON serializable' % (
                    type(o), repr(o)))

def download_file(box_client, scratch_dir, item, path):
    """
    Download a single file from box and save it to the scratch dir,
    respecting the file path relative to the original root directory
    :param box_client: Box API Client
    :param scratch_dir: Root folder where the files will be downloaded to
    :param item: The actual file object from Box
    :param path: Path to the root folder in Box
    """
    dest_folder = os.path.join(scratch_dir, path)
    os.makedirs(dest_folder, exist_ok=True)
    with open(os.path.join(dest_folder, item.name), 'wb') as dest_file:
        box_client.file(file_id=item.id).download_to(dest_file)


def download_folder(box_client, scratch_dir, folder, path=""):
    """
    Recursively download nested folders from box to a local directory.
    :param box_client: BOX Api Client
    :param scratch_dir: Root folder where the files will be downloaded to
    :param folder: The Box Folder Object where the files will be downloaded from
    :param path: Breadcrumbs back to the root folder for box
    :return:
    """
    for item in folder.get_items():
        if isinstance(item, Folder):
            download_folder(box_client, scratch_dir, item,
                            path=os.path.join(path, item.name))
        else:
            download_file(box_client, scratch_dir, item, path)


def zipdir(path, ziph):
    """
    Create a zipfile from a nested directory. Make the paths in the zip file
    relative to the root directory
    :param path: Path to the root directory
    :param ziph: zipfile handler
    :return:
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       arcname=os.path.join(os.path.relpath(root, path), file))


def max_temp(sample):
    """
    Find the maximum furnace temperature across all of the steps
    :param sample:
    :return: The max temperature or zero if there are no listed steps
    """
    step_temps = list(
        filter(None, list(map(lambda step: step.furnace_temperature,
                              sample.annealing_steps)) + \
               list(map(lambda step: step.furnace_temperature,
                        sample.growing_steps)) + \
               list(map(lambda step: step.furnace_temperature,
                        sample.cooling_steps))))

    if(len(step_temps)):
        return max(step_temps)
    else:
        return 0


def carbon_source(sample):
    if sample.growing_steps:
        list_of_sources = list(filter(None, list(map(lambda step: step.carbon_source, sample.growing_steps))))
        if len(list_of_sources):
            return list_of_sources[0]
        else:
            return ""
        return list(filter(None, list(map(lambda step: step.carbon_source, sample.growing_steps))))[0]
    else:
        return ""

# Get a handle to MDF Client Connect
mdfcc = MDFConnectClient(test=True, service_instance="dev")

# This will prompt for a developer Token from Box
# See https://developer.box.com/docs/authenticate-with-developer-token
client = DevelopmentClient()

# Download a hardcoded, specific folder from box for now
mdf_folder = client.folder("50410951565").get()

staging_folder = client.folder("59557678760").get()

filepath = "../data"
var_map = pd.read_csv(os.path.join(filepath, 'varmap2.csv')).to_dict()
data = pd.read_csv(os.path.join(filepath, 'recipe_2018_11_26.csv')).iloc[:-1, :]

col_names = data.columns

for i in range(data.shape[0]):
    s = sample()
    s.group = data.iloc[i, -4]
    s.sample_id = data.iloc[i, -3]
    s.experiment_date = str(data.iloc[i, -2])
    if s.experiment_date == 'nan':
        s.experiment_date = None

    s.contributor = data.iloc[i, -1]
    for j in range(30):
        value = data.iloc[i, j]
        if not pd.isnull(value):
            dbkey = var_map[col_names[j]][0]
            setattr(s, dbkey, value)

    # Annealing
    s.annealing_steps = []
    for step, j in enumerate(range(31, 109, 13)):
        prep = preparation_step()
        prep.name = "Annealing"
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i, j + p]
            dbkey = var_map[col_names[j + p]][0]
            if not pd.isnull(value):
                setattr(prep, dbkey, value)
        s.annealing_steps.append(prep)

    # Growing
    s.growing_steps = []
    for step, j in enumerate(range(109, 187, 13)):
        prep = preparation_step()
        prep.name = "Growing"
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i, j + p]
            dbkey = var_map[col_names[j + p]][0]
            if not pd.isnull(value):
                setattr(prep, dbkey, value)
        s.growing_steps.append(prep)

    # Cooling
    s.cooling_steps = []
    for step, j in enumerate(range(190, 266, 13)):
        prep = preparation_step()
        prep.name = "Cooling"
        prep.cooling_rate = data.iloc[i, 189]
        prep.sample_id = s.id
        prep.step = step
        for p in range(13):
            value = data.iloc[i, j + p]
            dbkey = var_map[col_names[j + p]][0]
            if not pd.isnull(value):
                setattr(prep, dbkey, value)
        s.cooling_steps.append(prep)

    with open(os.path.join("..", "output",
                           "%s-%s.json" % (s.material_name, s.identifier)),
              'w') as outfile:
        json.dump(s, outfile, cls=GresqEncoder)

    if s.experiment_date:
        print("----->" + s.identifier)
        print(max_temp(s))
        print(carbon_source(s))

        sample_folder = client.search().query(s.sample_id, type="folder").next()
        download_path = os.path.join("..", "output", s.sample_id)
        download_folder(client, download_path, sample_folder)
        with open(os.path.join(download_path, "recipe.json"), 'w') as outfile:
            json.dump(s, outfile, cls=GresqEncoder)

        zip_path = os.path.join("..", "output", s.sample_id + ".zip")
        zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        zipdir(download_path, zipf)
        zipf.close()

        box_file = staging_folder.upload(zip_path, s.sample_id + ".zip")

        experiment_date = datetime.strptime(s.experiment_date, "%Y-%m-%d")

        mdfcc.create_dc_block(title="Graphene Synthesis Sample "+s.identifier,
                              authors=[s.contributor],
                              affiliations=[s.group],
                              publication_year=experiment_date.year
                              )
        mdfcc.add_data(box_file.get_shared_link_download_url(access='open'))

        # Don't publish specific recipes. Later on, we will bundle datasets and
        # and publish an omnibus dataset
        # mdfcc.add_service("globus_publish")
        mdfcc.set_source_name(s.sample_id)

        submission = mdfcc.get_submission()

        submission["projects"] = {}
        submission["projects"]["nanomfg"] = {
            "catalyst": s.catalyst,
            "max_temperature": max_temp(s),
            "carbon_source": carbon_source(s),
            "base_pressure": s.base_pressure,
            "sample_surface_area": s.sample_surface_area,
            "sample_thickness": s.thickness,
            "orientation": "",
            "grain_size": ""
        }



        mdf_source_id = mdfcc.submit_dataset(submission=submission)
        print("Submitted to MDF -----> "+str(mdf_source_id))

        # print(str(mdfcc.check_status()))
        mdfcc.reset_submission()

