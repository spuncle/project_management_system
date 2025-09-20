import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-key-for-development-change-me')
SQLALCHEMY_DATABASE_URI = 'postgresql://projectuser:hld507@localhost/projectdb'

SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_HOST_STRICT = False
SERVER_NAME = '113.44.172.104:15688'