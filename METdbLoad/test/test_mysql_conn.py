import pymysql


def test_mysql_available():
    conn = pymysql.connect(host='127.0.0.1',
                    port=3306,
                    user='root',
                    password='root_password',
                    database='test_db',
                    )
    
    conn.cursor().execute("CREATE DATABASE mv_test")
    