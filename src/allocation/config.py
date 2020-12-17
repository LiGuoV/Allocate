import os


def get_api_url():
    host = os.environ.get('API_HOST', 'localhost')
    port = 5005 if host == 'localhost' else 80
    return f'http://{host}:{port}'


def get_db_uri():
    # return 'sqlite:///./db.db'
    host = os.environ.get('DB_HOST', '111.229.124.12')

    port = 54321 if host == 'localhost' else 5432
    password = os.environ.get('DB_PASSWORD','abc123')
    user, db_name = 'postgres', 'allocation'
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def get_redis_host_and_port():
    host = os.environ.get('REDIS_HOST', '111.229.124.12')
    port = 6379
    password = os.environ.get('DB_PASSWORD',)
    return dict(host=host, port=port,password=password)


def get_email_host_and_port():
    host = 'smtp.163.com'
    port = '465'
    password = 'UPNHJWVYYCGTGPYL'
    return dict(host=host, port=port, password=password)