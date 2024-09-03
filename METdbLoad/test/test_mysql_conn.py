import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='test_db',
                    port=3306,
                    user='root',
                    password='root_password')
    
    conn.cursor().execute("CREATE DATABASE mv_test")
    