import os

# 生成一个安全的密钥: python -c 'import secrets; print(secrets.token_hex(16))'
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_for_development_hld')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///../instance/project.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
