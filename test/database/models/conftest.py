
import pytest
from gresq.database import dal, Base
from gresq.database.models import Sample
from ..factories import SampleFactory

@pytest.fixture(scope="class")
def sample():
    """Set up a set of samples for testing using the factory boy factories.
    The sample factory cascades to all related tables. 
    """
    # create_all is already in test/database__init__.py. 
    #  I don't know why I have to call it here again, but I do.
    Base.metadata.create_all(bind=dal.engine)
    # Add some data here
    print("Hey, here come some samples...")
    yield SampleFactory.create_batch(5)
    # Drop and ditch
    print("Tearing down test samples and DB")
    with dal.session_scope(autocommit=True) as sess:
        for s in sess.query(Sample).all():
            sess.delete(s)
    Base.metadata.drop_all(bind=dal.engine)

@pytest.fixture(scope="class")
def all_sample_query():
    """Provide a query with all current samples
    
    Returns:
        Query: All samples
    """
    sesh =  dal.Session()
    return sesh.query(Sample).all()