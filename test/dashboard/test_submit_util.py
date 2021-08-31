# from faker import Faker
# from gresq.dashboard.submit.util import check_software_version, get_or_add_software_row
# from grdb.database.v1_1_0 import dal
# from grdb.database.v1_1_0.models import Software
# from gresq import __version__ as gresq_version
# from gsaimage import __version__ as gsaimage_version
# from gsaraman import __version__ as gsaraman_version

# fake = Faker()

# class TestSoftwareVersion:
#     def test_get_versions(self):
#         print()
#         print(f"gresq: {gresq_version}")
#         print(f"gsaimage: {gsaimage_version}")
#         print(f"gsaraman: {gsaraman_version}")

#     def test_check_software_version_none(self,sample):
#         row = check_software_version(dal.Session(), 'testsoft', '0.0.1')
#         assert row==None

#     def test_check_software_version_exists(self,sample):
#         session = dal.Session()
#         rows = session.query(Software).all()
#         #for r in rows:
#         #    print(r)
#         name = rows[0].name
#         version = rows[0].version
#         print()
#         print(f"name: {name}")
#         print(f"version: {version}")
#         row = check_software_version(session, name, version)
#         print(row)
#         assert row.name == name
#         assert row.version == version

#     def test_get_or_add_software_row_new(self):
#         session = dal.Session()
#         name = fake.last_name()
#         version = fake.first_name()
#         row = get_or_add_software_row(session, name, version)
#         assert row.name == name
#         assert row.version == version
#         print(row)


        
    


