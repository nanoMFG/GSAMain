from mdf_connect_client import MDFConnectClient
from datetime import datetime

class MDFAdaptor:
    def __init__(self):
        self.mdfcc = MDFConnectClient(test=True, service_instance="dev")

    def upload(self, recipe, box_file):
        experiment_date = datetime.now()

        self.mdfcc.create_dc_block(title="Graphene Synthesis Sample " + "TBD",
                                   authors=["TBD"],
                                   affiliations=["TBD"],
                                   publication_year=experiment_date.year
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



        # mdf_source_id = self.mdfcc.submit_dataset(submission=submission)
        # print("Submitted to MDF -----> "+str(mdf_source_id))
        #
        # self.mdfcc.reset_submission()
