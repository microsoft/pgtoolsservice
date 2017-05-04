import psycopg2

def connect(connectionstring):
    return psycopg2.connect(connectionstring)
