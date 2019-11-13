from boxsdk import JWTAuth, Client
from boxsdk.object.folder import Folder
from pprint import pprint
import os.path
import uuid
import logging

logger = logging.getLogger(__name__)


class BoxAdaptor:
    def __init__(self, path_to_config):
        print("box_config", path_to_config)
        if os.path.isfile(path_to_config) == False:
            raise ValueError(
                "configPath must be a path to the JSON config file for your Box JWT app"
            )
        auth = JWTAuth.from_settings_file(path_to_config)
        logger.info("Authenticating BoxAdaptor...")
        auth.authenticate_instance()
        self.client = Client(auth)

    def create_upload_folder(self, folder_name=None):
        if not folder_name:
            folder_name = str(uuid.uuid4())
        folder = self.client.folder(0).create_subfolder(folder_name)
        return folder

    def upload_file(self, box_folder, local_path, dest_file_name):
        logger.info(f"uploading: {dest_file_name}")
        logger.info(f"to: {box_folder}")
        logger.info(f"from: {local_path}")
        box_file = box_folder.upload(local_path, dest_file_name)
        return box_file

    def set_retention_policy(self, folder):
        policy = self.client.create_retention_policy(
            policy_name="auto_delete",
            disposition_action="permanently_delete",
            retention_length=1,
        )

        policy.assign(folder)
