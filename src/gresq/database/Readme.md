# GrResq Database Model Developer Documentation
```
__init__.py - Shared Declarative Base "Base" defined.
models - All database table models definitions
dal - Data access layer
model.py - Depricated
```

## Models

Models are defined in `./models` and are imported to the `models` package level.  Import as follows:
```
from gresq.database.models import Sample, Recipe
```

## Data Access Layer (DAL)
```
from gresq.database import dal
```

## Basic Queries

* Grab a session. Don;t really need the contex manger
* run the query.
```
session = dal.Session()
query = session.query(Model)
```

## Insert, Update or Delete
* Create a session context at the beginning of a logical operation (e.g. "submit").
* Pass the session in to various fuctions
* Allow the context manager to do the right thing (rollback or commit)
```
def submit_or_update_some_stuff():
    with dal.session_scope(autocommit=True) as session:
        do_stuff(session)
        do_more_stuff(session)
```

## Testing

Basic testing of the DB models is implemented using a set of `factory boy` factories to generate fake DB data.  When a SampleFactory is generated, all child models also generate.  

### Prerequistes
```
pytest
factory_boy
# set env. vars for DB
source env.sh
```

### Run the tests

##### Basic test run
```
pytest -v
```
##### See the outputs
```
pytest -v -s
```
##### Pick a test
```
pytest -v -s -k simple
```
