"""
Little script to force MDF to authenticate with Globus. This can be used
to generate a ~/.mdf/credentials folder on demand
"""
from mdf_connect_client import MDFConnectClient
mdfcc = MDFConnectClient(test=True, service_instance="dev")
