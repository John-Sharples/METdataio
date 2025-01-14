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


# Make sure the database name matches with the one you created on the database host
CONST_LOAD_DB_CMD = "use mv_mpr_orank_seeps"
TEST_DB = "mv_mpr_orank_seeps"

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
    # settings (hostname, username, etc.)
    yield conn

def test_db_created(setup_db):
    '''
       Verify that the mv_mpr_orank database was created
    Args:
        setup_db: db connection object

    Returns: None

    '''

    # connect to the database and verify the MPR and ORANK tables exist
    try:
        with setup_db.cursor() as cursor:
            # Check that the line_data_mpr and line_data_orank
            # tables were created
            cursor.execute(CONST_LOAD_DB_CMD)
            check_db_exists_query = "show databases;"
            cursor.execute(check_db_exists_query)


        # Get all rows
        rows = cursor.fetchall()
        list_of_rows = [r[0] for r in rows]
        assert TEST_DB in list_of_rows


    finally:
      setup_db.close()


def test_tables_created(setup_db):
    
    # connect to the database and verify the MPR and ORANK tables exist
    try:
        with setup_db.cursor() as cursor:
            # Check that the line_data_mpr and
            # line_data_orank tables were created
            cursor.execute(CONST_LOAD_DB_CMD)
            check_db_exists_query = "show tables;"
            cursor.execute(check_db_exists_query)


        # Get all rows
        rows = cursor.fetchall()
        list_of_rows = [r[0] for r in rows]
        print(f"list of rows: {list_of_rows}")
        assert 'line_data_mpr' in list_of_rows
        assert 'line_data_orank' in list_of_rows

    finally:
      setup_db.close()


def test_mpr_columns(setup_db):
   # log into the database and verify the renamed columns are in the
   # list_data_mpr database table, the previous/replaced columns do NOT
   # exist, and the new columns exist.

    try:
        with setup_db.cursor() as cursor:
            cursor.execute(CONST_LOAD_DB_CMD)
            check_columns_exist = "desc line_data_mpr;"
            cursor.execute(check_columns_exist)

            # Get all rows
            rows = cursor.fetchall()
            list_of_rows = [r[0] for r in rows]
            print(f"list of rows:\n{list_of_rows}")
            assert 'obs_climo_mean' in list_of_rows
            assert 'obs_climo_stdev' in list_of_rows
            assert 'obs_climo_cdf' in list_of_rows
            assert 'fcst_climo_mean' in list_of_rows
            assert 'fcst_climo_stdev' in list_of_rows


    finally:
        setup_db.close()


def test_orank_columns(setup_db):
   # log into the database and verify the renamed and new columns are in the
   # list_data_orank database table, and the previous/replaced columns no longer
   # exist.

    try:
        with setup_db.cursor() as cursor:
            cursor.execute(CONST_LOAD_DB_CMD)
            check_columns_exist = "desc line_data_orank;"
            cursor.execute(check_columns_exist)

            # Get all rows
            rows = cursor.fetchall()
            list_of_rows = [r[0] for r in rows]
            assert 'obs_climo_mean' in list_of_rows
            assert 'obs_climo_stdev' in list_of_rows
            assert 'fcst_climo_mean' in list_of_rows
            assert 'fcst_climo_stdev' in list_of_rows

    finally:
        setup_db.close()

def test_seeps_columns(setup_db):
   # log into the database and verify the renamed SEEPS columns are in the
   # list_data_seeps database table, and the previous/replaced columns no longer
   # exist.

    try:
        with setup_db.cursor() as cursor:
            cursor.execute(CONST_LOAD_DB_CMD)
            check_columns_exist = "desc line_data_seeps;"
            cursor.execute(check_columns_exist)

            # Get all rows
            rows = cursor.fetchall()
            list_of_rows = [r[0] for r in rows]

            # Verify newly renamed columns exist in the updated data
            assert 'odfl' in list_of_rows
            assert 'odfh' in list_of_rows
            assert 'olfd' in list_of_rows
            assert 'olfh' in list_of_rows
            assert 'ohfd' in list_of_rows
            assert 'ohfl' in list_of_rows

            # Verify that remaining columns are unchanged in the updated data
            assert 'pf1' in list_of_rows
            assert 'pf2' in list_of_rows
            assert 'pf3' in list_of_rows
            assert 'pv1' in list_of_rows
            assert 'pv2' in list_of_rows
            assert 'pv3' in list_of_rows

    finally:
        setup_db.close()

