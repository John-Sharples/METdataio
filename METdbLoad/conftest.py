import pytest
import sys
import os
import pymysql
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from METdataio.METdbLoad.ush.read_data_files import ReadDataFiles

logger = logging.getLogger(__name__)

# add METdataio directory to path so packages can be found
top_dir = str(Path(__file__).parents[1])
sys.path.insert(0, os.path.abspath(top_dir))


def maria_conn():
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='root_password',
        )
    
    except Exception as e:
        # Test run will fail if db is not found.
        # TODO: If we want to run tests that don't require a db when db is missing
        # we could put pytest.skip here instead of raising the exception.
        logger.error("Failed to create database connection.")
        raise e
    
    return conn


def get_empty_db_conn():
    conn = maria_conn()

    with conn.cursor() as cur:
        cur.execute("DROP DATABASE IF EXISTS mv_test;")
        cur.execute("CREATE DATABASE mv_test;")
    conn.commit()
    conn.close()

    db_conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='root_password',
            database='mv_test',
            autocommit=True,
        )
    
    with db_conn.cursor() as cur:
        cur.execute(sql_string)
    
    yield db_conn

    db_conn.close()


@pytest.fixture
def emptyRunSql():
    """Patch RunSql with an empty db"""

    from METdataio.METdbLoad.ush import run_sql

    class testRunSql(run_sql.RunSql):

        def sql_on(self, connection):
            self.local_infile = "ON"
            self.conn = get_empty_db_conn()
            self.cur = self.conn.cursor()

    with patch.object(run_sql, "RunSql", return_value=testRunSql()):
        yield run_sql.RunSql()


# This is a sample of data copied from test file point_stat_DUP_SINGLE_120000L_20120409_120000V.stat
# found in the METviewer test data.
# TODO: expand this to include other data (e.g. linetypes, met tools, etc.). Probably need to load this from
# disk rather than storing here as a string.
POINT_STAT_DATA = """VERSION MODEL FCST_LEAD FCST_VALID_BEG  FCST_VALID_END  OBS_LEAD OBS_VALID_BEG   OBS_VALID_END   FCST_VAR FCST_LEV OBS_VAR OBS_LEV OBTYPE VX_MASK INTERP_MTHD INTERP_PNTS FCST_THRESH OBS_THRESH COV_THRESH   ALPHA LINE_TYPE
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_120000 20120409_120000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1          NA         NA         NA      NA MPR       2         1       001  43.00000 -89.00000 NA 2.00000 275.71640 293.00000 NA NA
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_120000 20120409_120000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1          NA         NA         NA      NA MPR       2         2       002  46.00000 -92.00000 NA 2.00000 272.71640 293.00000 NA NA
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_103000 20120409_133000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1     >=5.000    >=5.000         NA      NA FHO       2   1.00000   1.00000   1.00000
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_103000 20120409_133000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1     >=5.000    >=5.000         NA      NA CTC       2         2         0         0         0
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_103000 20120409_133000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1     >=5.000    >=5.000         NA 0.05000 CTS       2   1.00000   0.34238   1.00000        NA NA 1.00000   0.34238   1.00000 NA NA   1.00000   0.34238   1.00000 NA NA 1.00000      NA      NA 1.00000 0.34238 1.00000 NA NA NA NA NA NA NA NA NA        NA        NA      NA 0.00000 0.00000 0.65762      NA       NA 1.00000 0.34238 1.00000 NA NA       NA NA NA        NA NA NA      NA NA NA       NA NA NA        NA NA NA        NA NA NA        NA NA NA        NA NA NA        NA NA NA      NA NA NA      NA NA NA NA NA NA NA NA NA NA NA NA NA NA NA NA NA NA NA
V4.2    WRF   120000    20120409_120000 20120409_120000 000000   20120409_103000 20120409_133000 TMP      Z2       TMP     Z2      ADPSFC FULL    UW_MEAN               1          NA         NA         NA 0.05000 CNT       2 274.21640 255.15709 293.27571        NA NA 2.12132   0.94643  67.69167 NA NA 293.00000 293.00000 293.00000 NA NA 0.00000 0.00000 0.00000      NA      NA      NA NA NA NA NA NA NA  0  0  0 -18.78360 -37.84291 0.27571      NA      NA 2.12132 0.94643 67.69167      NA      NA 0.93589 NA NA 18.78360 NA NA 355.07362 NA NA 2.25000 NA NA 18.84340 NA NA -19.98360 NA NA -19.53360 NA NA -18.78360 NA NA -18.03360 NA NA -17.58360 NA NA 1.50000 NA NA 1.50000 NA NA
"""


def _populate_xml_load_spec(met_data_dir,
                            met_tool="point_stat",
                            host="192.168.0.42"):
    """Return the xml load specification with substitute values.
    """
    #TODO: determine if other tags require substitution as well
    return f"""<load_spec>
    <connection>
        <management_system>mysql</management_system>
        <host>{host}:3306</host>
        <database>mv_load_test</database>
        <user>user</user>
        <password>user_pwd</password>
    </connection>

    <folder_tmpl>{met_data_dir}</folder_tmpl>
    <verbose>true</verbose>
    <insert_size>1</insert_size>
    <stat_header_db_check>true</stat_header_db_check>
    <mode_header_db_check>false</mode_header_db_check>
    <mtd_header_db_check>false</mtd_header_db_check>
    <drop_indexes>false</drop_indexes>
    <apply_indexes>false</apply_indexes>
    <load_stat>true</load_stat>
    <load_mode>false</load_mode>
    <load_mtd>false</load_mtd>
    <load_mpr>true</load_mpr>
    <load_orank>true</load_orank>
    <load_val>
        <field name="met_tool">
        <val>{met_tool}</val>
        </field>
    </load_val>
    <group>Testing</group>
    <description>testing DB load</description>
    </load_spec>"""


@pytest.fixture
def stat_file_dir(tmp_path):
    """Write test stat file and return parent dir."""
    stat_files_dir = tmp_path / "stat_files"
    stat_files_dir.mkdir()
    
    stat_file = stat_files_dir / "point_stat.stat"
    with open(stat_file, "w") as text_file:
        text_file.write(POINT_STAT_DATA)
    return stat_files_dir


#TODO: see if we can restrict the scope of this fixture.
@pytest.fixture
def get_xml_test_file(tmp_path, stat_file_dir):
    """Write test_load_specification.xml and return path"""
    xml_path = tmp_path / "test_load_specification.xml"
    with open(xml_path, "w") as text_file:
        text_file.write(_populate_xml_load_spec(stat_file_dir))
    return xml_path



@pytest.fixture
def get_xml_loadfile(get_xml_test_file):
    def load_and_read_xml():
        from METdataio.METdbLoad.ush.read_load_xml import XmlLoadFile

        XML_FILE = get_xml_test_file
        XML_LOADFILE = XmlLoadFile(XML_FILE)
        XML_LOADFILE.read_xml()
        return XML_LOADFILE

    return load_and_read_xml


@pytest.fixture
def get_file_data(get_xml_loadfile):
    """Return a test ReadDataFile object"""

    XML_LOADFILE = get_xml_loadfile()
    FILE_DATA = ReadDataFiles()
    FILE_DATA.read_data(XML_LOADFILE.flags,
                        XML_LOADFILE.load_files,
                        XML_LOADFILE.line_types)

    return FILE_DATA
