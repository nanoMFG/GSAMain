from sqlalchemy.sql.expression import and_
from ...database.models import Software


def get_software_version_details(row):
    """Pass in a Software row with only name and version
    
    Args:
        row ([type]): [description]
    
    Returns:
        Software row: Row with added details
    """
    # Release date

    # branch

    # commitsh

    # url
    return row


def check_software_version(session, name, version):
    """Check whether the name version strings are keys in the Software table.
    Return the row as a dictionary, or insert a new software row and return that.

    
    Args:
        session (Session): Sqlalchemy session
        name (str): Software name
        version (str): Software version
    
    Returns:
        Software(row) or None: [description]
    """
    row = (
        session.query(Software)
        .filter(Software.name == name, Software.version == version)
        .one_or_none()
    )

    return row


def get_or_add_software_row(session, name, version):
    row = check_software_version(session, name, version)
    if not row:
        row = Software(name=name, version=version)
        row = get_software_version_details(row)
        session.add(row)
        session.flush()
    return row
