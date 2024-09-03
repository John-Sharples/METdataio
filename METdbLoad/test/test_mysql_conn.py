import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='localhost',
                       user='test',
                       password='test')
    
    conn.cursor().execute("CREATE DATABASE mv_test")
    