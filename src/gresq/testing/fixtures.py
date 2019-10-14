import os
import pytest

@pytest.fixture
def unset_env_vars():
    """unset environment and secrets file to test defaults
    """
    for k in vars_dict.keys():
        val = os.getenv(k)
        if val:
            vars_dict[k] = val
            os.unsetenv(k)
            del os.environ[k]

    yield

    # Teardown, put things back the way they were...
    for k, v in vars_dict.items():
        if vars_dict[k] != '':
            os.putenv(k, v)
            setattr(os.environ,k,v)
        vars_dict[k] = ''
