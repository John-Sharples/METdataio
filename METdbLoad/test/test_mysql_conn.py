import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='test_db',
                    port=3306,
                    user='test_user',
                    password='test_password')
    
    conn.cursor().execute("CREATE DATABASE mv_test")
    