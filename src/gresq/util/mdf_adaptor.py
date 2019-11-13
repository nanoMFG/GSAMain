from mdf_connect_client import MDFConnectClient
from datetime import datetime
import uuid


class MDFException(Exception):
    """Exceptions related to the MDF Service"""


class MDFAdaptor:
    def __init__(self):
        self.mdfcc = MDFConnectClient(test=True, service_instance="prod")

    def upload_recipe(self, recipe, box_file):
        experiment_date = datetime.now()

        self.mdfcc.create_dc_block(
            title="Graphene Synthesis Sample " + "TBD",
            authors=[
                "%s, %s" % (auth["last_name"], auth["first_name"])
                for auth in recipe.authors
            ],
            affiliations=[auth["institution"] for auth in recipe.authors],
            publication_year=recipe.experiment_year,
        )
        self.mdfcc.add_data_source(box_file.get_shared_link_download_url(access="open"))

        # Don't publish specific recipes. Later on, we will bundle datasets and
        # and publish an omnibus dataset
        # mdfcc.add_service("globus_publish")
        self.mdfcc.set_source_name(str(uuid.uuid4()))

        submission = self.mdfcc.get_submission()

        submission["projects"] = {}
        submission["projects"]["nanomfg"] = {
            "catalyst": recipe.catalyst,
            "max_temperature": recipe.max_temp(),
            "carbon_source": recipe.carbon_source(),
            "base_pressure": recipe.base_pressure
            # "sample_surface_area": recipe.sample_surface_area,
            # "sample_thickness": recipe.thickness,
            # "orientation": "",
            # "grain_size": ""
        }

        print("\n\n\n\n------>", submission)

        try:
            mdf_result = self.mdfcc.submit_dataset(submission=submission)
        except Exception as e:
            print("Exception submitting dataset to mdf ", str(e))
            raise MDFException(e)

        if not mdf_result["success"]:
            self.mdfcc.reset_submission()
            print("\n\n\n--->Error-----> " + mdf_result["error"])
            raise MDFException(mdf_result["error"])

        print("Submitted to MDF -----> " + str(mdf_result))
        self.mdfcc.reset_submission()
        return mdf_result["source_id"]

    def upload_raman_analysis(
        self, recipe, recipe_dataset_id, raman_set, raman_box_file
    ):

        self.mdfcc.create_dc_block(
            title="Graphene Synthesis Raman Analysis",
            authors=[
                "%s, %s" % (auth["last_name"], auth["first_name"])
                for auth in recipe.authors
            ],
            affiliations=[auth["institution"] for auth in recipe.authors],
            publication_year=recipe.experiment_year,
            related_dois=recipe_dataset_id,
        )
        self.mdfcc.add_data_source(
            raman_box_file.get_shared_link_download_url(access="open")
        )

        self.mdfcc.set_source_name(str(uuid.uuid4()))

        submission = self.mdfcc.get_submission()

        submission["projects"] = {}
        submission["projects"]["nanomfg"] = {
            "d_to_g": raman_set["d_to_g"],
            "gp_to_g": raman_set["gp_to_g"],
            "d_peak_shift": raman_set["d_peak_shift"],
            "d_peak_amplitude": raman_set["d_peak_amplitude"],
            "d_fwhm": raman_set["d_fwhm"],
            "g_peak_shift": raman_set["g_peak_shift"],
            "g_peak_amplitude": raman_set["g_peak_amplitude"],
            "g_fwhm": raman_set["g_fwhm"],
            "g_prime_peak_shift": raman_set["g_prime_peak_shift"],
            "g_prime_peak_amplitude": raman_set["g_prime_peak_amplitude"],
            "g_prime_fwhm": raman_set["g_prime_fwhm"],
        }

        print("\n\n\n\n------>", submission)

        try:
            mdf_result = self.mdfcc.submit_dataset(submission=submission)
        except Exception as e:
            print("Exception submitting raman analysis dataset to mdf ", str(e))
            raise MDFException(e)

        if not mdf_result["success"]:
            self.mdfcc.reset_submission()
            print("\n\n\n--->Error-----> " + mdf_result["error"])
            raise MDFException(mdf_result["error"])

        print("Submitted raman analysis to MDF -----> " + str(mdf_result))
        self.mdfcc.reset_submission()
        return mdf_result["source_id"]
