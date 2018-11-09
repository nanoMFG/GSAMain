
def init():
    from gresq.config import config
    from gresq.database import dal

    dal.init_db(config['development'])

def load_csv():
    from gresq.citrine_data import cm
    from gresq.database import Base,dal

    cm.show_column_map()
    print(cm.nrows)

    Base.metadata.drop_all(bind=dal.engine)
    Base.metadata.create_all(bind=dal.engine)

    with dal.session_scope() as session:
        for row in range(cm.nrows):
            #print (row)
            cm.import_csv(row,session)

