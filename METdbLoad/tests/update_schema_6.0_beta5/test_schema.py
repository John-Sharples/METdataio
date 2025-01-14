import pytest
import pymysql
import yaml
from dataclasses import make_dataclass

#######################################################################
# These tests can only be run on the host where the database is running.
# Pre-condition:
#     The data in the accompanying data directory ./Data, should
#     already be loaded in the database using the corresponding
#     schema: mv_mysql.sql and the appropriate xml specification file.
#     This is to avoid having the password visible in the test code.
#

CONST_LOAD_DB_CMD = "use mv_load_test"


@pytest.fixture
def setup_db():
    """
          Read in the config file to retrieve the database login information.

    """
    config_file = 'test_loading.yaml'
    with open(config_file, 'r') as stream:
        try:
            parms: dict = yaml.load(stream, Loader=yaml.FullLoader)
            # pathlib.Path(parms['output_dir']).mkdir(parents=True, exist_ok=True)
        except yaml.YAMLError as exc:
            print(exc)

    # Create a dataclass of the database information
    DBS = make_dataclass("DBS", ["hostname", "port",  "username", "password", "dbname"])
    db_settings = DBS(parms['hostname'], parms['port'], parms['username'], parms['password'], parms['dbname'])

    # Return the db connection object
    conn = pymysql.connect(
        host=db_settings.hostname,
        port=db_settings.port,
        user=db_settings.username,
        password=db_settings.password,
        db=db_settings.dbname,
        charset='utf8mb4'
    )
    ## settings (hostname, username, etc.)
    yield conn


def test_db_created(setup_db):
    '''
       Verify that the mv_load_test database was created
    Args:
        setup_db: db connection object

    Returns: None

    '''

    # connect to the database and verify the VCNT, VL1L2, and VAL1L2 tables exist
    try:
        with setup_db.cursor() as cursor:
            # Check that the line_data_vcnt, line_data_vl1l2, and
            # line_data_val1l2 tables were created
            cursor.execute(CONST_LOAD_DB_CMD)
            check_db_exists_query = "show databases;"
            cursor.execute(check_db_exists_query)


        # Get all rows
        rows = cursor.fetchall()
        list_of_rows = [r[0] for r in rows]
        assert 'mv_load_test' in list_of_rows


    finally:
      setup_db.close()

def test_tables_created(setup_db):
    
    # connect to the database and verify the VCNT, VL1L2, and VAL1L2 tables exist
    try:
        with setup_db.cursor() as cursor:
            # Check that the line_data_vcnt, line_data_vl1l2, and
            # line_data_val1l2 tables were created
            cursor.execute(CONST_LOAD_DB_CMD)
            check_db_exists_query = "show tables;"
            cursor.execute(check_db_exists_query)


        # Get all rows
        rows = cursor.fetchall()
        list_of_rows = [r[0] for r in rows]
        assert 'line_data_vcnt' in list_of_rows
        assert 'line_data_vl1l2' in list_of_rows
        assert 'line_data_val1l2' in list_of_rows

    finally:
      setup_db.close()


def test_vl1l2_columns(setup_db):
   # log into the database and verify the total_dir column is in the
   # list_data_vl1l2 database table.

    try:
        with setup_db.cursor() as cursor:
            cursor.execute(CONST_LOAD_DB_CMD)
            check_columns_exist = "desc line_data_vl1l2;"
            cursor.execute(check_columns_exist)

            # Get all rows
            rows = cursor.fetchall()
            list_of_rows = [r[0] for r in rows]
            assert 'total_dir' in list_of_rows

    finally:
        setup_db.close()


def test_val1l2_columns(setup_db):
   # log into the database and verify the total_dir column is in the
   # list_data_val1l2 database table.

    try:
        with setup_db.cursor() as cursor:
            cursor.execute(CONST_LOAD_DB_CMD)
            check_columns_exist = "desc line_data_val1l2;"
            cursor.execute(check_columns_exist)

            # Get all rows
            rows = cursor.fetchall()
            list_of_rows = [r[0] for r in rows]
            assert 'total_dir' in list_of_rows

    finally:
        setup_db.close()

def test_vcnt_columns(setup_db):
            # log into the database and verify the total_dir column is in the
            # list_data_vcnt database table.

            try:
                with setup_db.cursor() as cursor:
                    cursor.execute(CONST_LOAD_DB_CMD)
                    check_columns_exist = "desc line_data_vcnt;"
                    cursor.execute(check_columns_exist)

                    # Get all rows
                    rows = cursor.fetchall()
                    list_of_rows = [r[0] for r in rows]
                    assert 'total_dir' in list_of_rows

            finally:
                setup_db.close()
