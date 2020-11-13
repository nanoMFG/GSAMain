# Copyright (c) 2019, IRIS-HEP
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import json
import os
import sys
import uuid

from gresq.database.models import sample, Sample
from gresq.database import dal
from gresq.config import config
# import pandas as pd
from gresq.recipe import Recipe
from gresq.util.box_adaptor import BoxAdaptor
from gresq.util.mdf_adaptor import MDFAdaptor
import urllib.request


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
                       arcname=os.path.join(os.path.relpath(root, path),
                                            file))


box_config_path = "box_config.json"

def stage_upload(sample, sem_files=[], raman_files=[], json_name='mdf'):
    import zipfile, time, shutil

    mdf_dir = 'mdf_%s_%s' % (json_name, time.time())
    os.mkdir(mdf_dir)
    mdf_path = os.path.abspath(mdf_dir)

    dump_file = open(os.path.join(mdf_path, '%s.json' % json_name), 'w')
    json.dump(sample, dump_file)
    dump_file.close()

    for raman_file in raman_files:
        print(raman_file.url, raman_file.filename)
        urllib.request.urlretrieve(raman_file.url, mdf_path+"/"+raman_file.filename)
    for sem_file in sem_files:
        print(sem_file.url, sem_file.filename)
        urllib.request.urlretrieve(sem_file.url, mdf_path+"/"+sem_file.filename)

    box_adaptor = BoxAdaptor(box_config_path)
    upload_folder = box_adaptor.create_upload_folder()

    zip_path = mdf_path + ".zip"
    zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(mdf_path, zipf)
    zipf.close()
    print("Uploading ", zip_path, " to box")

    box_file = box_adaptor.upload_file(upload_folder, zip_path,
                                       mdf_dir + '.zip')

    return box_file


def upload_recipe(sample_dict, box_file):
    mdf = MDFAdaptor()
    return mdf.upload_recipe(Recipe(sample_dict), box_file)


def upload_raman(sample_dict, sample_id, raman_json, raman_box_file):
    mdf = MDFAdaptor()
    return mdf.upload_raman_analysis(Recipe(sample_dict), sample_id, raman_json, raman_box_file)

def get_status(source_id):
    mdf = MDFAdaptor()
    return mdf.get_status(source_id)


def upload_file(file_path, folder_name=None):
    box_adaptor = BoxAdaptor(box_config_path)
    upload_folder = box_adaptor.create_upload_folder(folder_name=folder_name)
    box_file = box_adaptor.upload_file(upload_folder, file_path,
                                       str(uuid.uuid4()))

    return box_file.get_shared_link_download_url(access='open')


dal.init_db(config['production'])

with dal.session_scope() as session:
    samples = session.query(Sample)
    print(samples)
    for sample in samples:
        if sample.raman_files and len(sample.raman_files) > 0:

            print(sample.id)
            sample_dict = sample.json_encodable()

            recipe_box_file = stage_upload(sample_dict,
                                           raman_files=sample.raman_files,
                                           sem_files=sample.sem_files,
                                           json_name='mdf')

            recipe_result = upload_recipe(sample_dict, recipe_box_file)
            print("Recipe --> ",recipe_result)
            print(get_status(recipe_result))

            raman_json = sample.raman_analysis.json_encodable()
            raman_json['peaks'] = [
                {
                    "label": "g",
                    "width": raman_json['g_fwhm']['value'],
                    "center": raman_json['g_peak_shift']['value']
                },
                {
                    "label": "g_prime",
                    "width": raman_json['g_prime_fwhm']['value'],
                    "center": raman_json['g_prime_peak_shift']['value']

                },
                {
                    "label": "d",
                    "width": raman_json['d_fwhm']['value'],
                    "center": raman_json['d_peak_shift']['value']

                }
            ]
            raman_json['ratios'] = [
                {
                    "peak1": "d",
                    "peak2": "g",
                    "ratio": raman_json['d_to_g']['value:']
                },
                {
                    "peak1": "g_prime",
                    "peak2": "g",
                    "ratio": raman_json['gp_to_g']['value:']
                },
            ]

            raman_box_file = stage_upload(raman_json, json_name='raman')
            raman_result = upload_raman(sample_dict, recipe_result, raman_json, raman_box_file)

            print("====> ", raman_result)
            print(get_status(raman_result))
