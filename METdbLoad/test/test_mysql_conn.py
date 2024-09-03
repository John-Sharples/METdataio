import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='127.0.0.1',
                    port=3306,
                    user='test_user',
                    password='test_password')
    
    conn.cursor().execute("CREATE DATABASE mv_test")
    