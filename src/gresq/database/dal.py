"""DataAccessLayer module.
Defines the DataAccessLayer class and initializes an instance of the class to be
used by the application.
"""
import ast
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from grdb.database.v1_1_0 import Base

# Uncomment to hav all SQL dumped to the console.
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class DataAccessLayer:
    def __init__(self):
        """ Define data access layer attributes."""
        self.engine = None
        self.Session = None
        self.privileges = {"read": True, "write": False, "validate": False}

    def init_db(
        self, config, privileges={"read": True, "write": False, "validate": False}
    ):
        """Initialize database connection for a given configuration.

        Args:
            config (gresq.Config): Configuration object.
            privileges (dict): Dictionary of access privileges.
        """
        self.privileges = privileges
        if config.DATABASEARGS is None:
            self.engine = create_engine(config.DATABASEURI)
        else:
            self.engine = create_engine(
                config.DATABASEURI, connect_args=ast.literal_eval(config.DATABASEARGS)
            )
        Base.metadata.create_all(bind=self.engine)
        self.Session = scoped_session(
            sessionmaker(autocommit=False, autoflush=True, bind=self.engine)
        )
        Base.query = self.Session.query_property()

    def abort_ro(self, *args, **kwargs):
        return

    @contextmanager
    def session_scope(self, autocommit=False):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        if self.privileges["write"] == False:
            session.flush = self.abort_ro
        try:
            yield session
            if autocommit:
                session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()


dal = DataAccessLayer()
"""DataAccessLayer: Initialize a blank instance of the DataAccessLayer class
"""
