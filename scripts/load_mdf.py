import json
import pandas as pd
import os

from boxsdk.object.folder import Folder

from gresq.database import sample, GresqEncoder
from src.gresq.database import preparation_step
from boxsdk import JWTAuth, DevelopmentClient
import zipfile

"""
NAME:
    load_mdf
    
SYNOPSIS:
    Read data from the recipe CSV file and create datasets in Materials Data
    Facility.
    
DESCRIPTION:
    For now this script just reads the CSV file and generates JSON documents
    for each recipie. These documents are written to the output folder.
    
    Can read a specific root folder in Box to create a zip file that will be 
    uploaded to MDF as part of the dataset.
"""


def download_file(client, scratch_dir, item, path):
    """
    Download a single file from box and save it to the scratch dir,
    respecting the file path relative to the original root directory
    :param client: Box API Client
    :param scratch_dir: Root folder where the files will be downloaded to
    :param item: The actual file object from Box
    :param path: Path to the root folder in Box
    """
    dest_folder = os.path.join(scratch_dir, path)
    os.makedirs(dest_folder, exist_ok=True)
    with open(os.path.join(dest_folder, item.name), 'wb') as dest_file:
        client.file(file_id=item.id).download_to(dest_file)


def download_folder(client, scratch_dir, folder, path=""):
    """
    Recursively download nested folders from box to a local directory.
    :param client: BOX Api Client
    :param scratch_dir: Root folder where the files will be downloaded to
    :param folder: The Box Folder Object where the files will be downloaded from
    :param path: Breadcrumbs back to the root folder for box
    :return:
    """
    for item in folder.get_items():
        if isinstance(item, Folder):
            download_folder(client, scratch_dir, item,
                            path=os.path.join(path, item.name))
        else:
            download_file(client, scratch_dir, item, path)


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

# This will prompt for a developer Token from Box
# See https://developer.box.com/docs/authenticate-with-developer-token
client = DevelopmentClient()

# Download a hardcoded, specific folder from box for now
mdf_folder = client.folder("50410951565").get()
download_folder(client, "/tmp/mdf", mdf_folder)

zipf = zipfile.ZipFile('/tmp/mdf.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir('/tmp/mdf', zipf)
zipf.close()


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
