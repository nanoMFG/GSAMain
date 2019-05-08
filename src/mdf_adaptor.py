from mdf_connect_client import MDFConnectClient
from datetime import datetime

class MDFAdaptor:
    def __init__(self):
        self.mdfcc = MDFConnectClient(test=True, service_instance="prod")

    def upload(self, recipe, box_file):
        experiment_date = datetime.now()

        self.mdfcc.create_dc_block(title="Graphene Synthesis Sample " + "TBD",
                                   authors=["%s, %s"%(auth['last_name'],auth['first_name']) for auth in recipe.authors],
                                   affiliations=[auth['institution'] for auth in recipe.authors],
                                   publication_year=recipe.experiment_year
                                   )
        self.mdfcc.add_data(box_file.get_shared_link_download_url(access='open'))

        # Don't publish specific recipes. Later on, we will bundle datasets and
        # and publish an omnibus dataset
        # mdfcc.add_service("globus_publish")
        self.mdfcc.set_source_name("TBD")

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

        print("\n\n\n\n------>",submission)

        mdf_result = self.mdfcc.submit_dataset(submission=submission)
        if not mdf_result["success"]:
            self.mdfcc.reset_submission()
            print("\n\n\n--->Error-----> "+mdf_result['error'])
            return mdf_result["error"]

        print("Submitted to MDF -----> "+str(mdf_result))
        self.mdfcc.reset_submission()
        return None
