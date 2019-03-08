import psycopg2

PGHOST = '127.0.0.1'
PGDATABASE = 'test_rest'
PGUSER = 'postgres'
PGPASSWORD = 'FMpGeUGPBsUgJvRLs3QP9'

pgconn = psycopg2.connect(host=PGHOST, database=PGDATABASE, user=PGUSER, password=PGPASSWORD, port=5432)

cursor = pgconn.cursor()

# cursor.execute('SELECT *FROM auth_user')

# print(cursor.fetchall())
