from db import get_db

db = get_db()

def db_connect(func):
    '''Decorator to connect to the database if not already connected'''
    def connect(*args, **kwargs):
        if not db.is_connected():
            db.connect()
        return func(*args, **kwargs)
    return connect

@db_connect
def send_query(query, args):
    '''Send a query to the database'''
    cur = db.cursor()
    cur.execute(query, args)
    result = cur.fetchall()
    db.commit()
    return result

@db_connect
def send_upload_post(args):
    '''Upload a post to the database'''
    cur = db.cursor()
    cur.callproc("uploadPost", args)
    result = cur.fetchall()
    db.commit()
    return result

@db_connect
def send_get_posts(args):
    '''Get posts from the database'''
    cur = db.cursor()
    cur.callproc("getPosts", args)
    result = [r.fetchall() for r in cur.stored_results()]
    db.commit()
    return result[0]

def close_db():
    '''Close the database connection'''
    db.close()