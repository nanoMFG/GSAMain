import sys
sys.path.append("../src")
from grdb.database.v1_1_0 import dal, Base
from gresq.config import config

print('dev default URI: ' + config['development'].DATABASEURI)
print('dev default ARGS: ' + str(config['development'].DATABASEARGS))
if hasattr(config['development'],'read'):
    print('dev read URI: ' + config['development'].read.DATABASEURI)
    print('dev read ARGS: ' + str(config['development'].read.DATABASEARGS))
if hasattr(config['development'],'write'):
    print('dev write URI: ' + config['development'].write.DATABASEURI)
    print('dev write ARGS: ' + str(config['development'].write.DATABASEARGS))
if hasattr(config['development'],'admin'):
    print('dev admin URI: ' + config['development'].admin.DATABASEURI)
    print('dev admin ARGS: ' + str(config['development'].admin.DATABASEARGS))

print('test default URI: ' + config['test'].DATABASEURI)
print('test default ARGS: ' + str(config['test'].DATABASEARGS))
if hasattr(config['test'],'read'):
    print('test read URI: ' + config['test'].read.DATABASEURI)
    print('test read ARGS: ' + str(config['test'].read.DATABASEARGS))
if hasattr(config['test'], 'write'):
    print('test write URI: ' + config['test'].write.DATABASEURI)
    print('test write ARGS: ' + str(config['test'].write.DATABASEARGS))
if hasattr(config['test'], 'admin'):
    print('test admin URI: ' + config['test'].admin.DATABASEURI)
    print('test admin ARGS: ' + str(config['test'].admin.DATABASEARGS))

print('prod default URI: ' + config['production'].DATABASEURI)
print('prod default ARGS: ' + str(config['production'].DATABASEARGS))
if hasattr(config['production'],'read'):
    print('prod read URI: ' + config['production'].read.DATABASEURI)
    print('prod read ARGS: ' + str(config['production'].read.DATABASEARGS))
if hasattr(config['production'],'write'):
    print('prod write URI: ' + config['production'].write.DATABASEURI)
    print('prod write ARGS: ' + str(config['production'].write.DATABASEARGS))
if hasattr(config['production'],'admin'):
    print('prod admin URI: ' + config['production'].admin.DATABASEURI)
    print('prod admin ARGS: ' + str(config['production'].admin.DATABASEARGS))

#config['development'].get_users()

#dal.init_db(config['development'].read)

#Base.metadata.drop_all(bind=dal.engine)
#Base.metadata.create_all(bind=dal.engine)
