import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='127.0.0.1',
                       user='test',
                       password='test')
    
    conn.cursor().execute("CREATE DATABASE mv_test")
