import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 重定向到登录页面的路由
login_manager.login_message_category = 'info'
login_manager.login_message = '请先登录以访问此页面。'

def create_app():
    """Application factory function."""
    app = Flask(__name__, instance_relative_config=True)

    # 加载配置
    app.config.from_pyfile('config.py', silent=True)

    # 初始化扩展
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # 导入蓝图
        from .auth import routes as auth_routes
        from .main import routes as main_routes
        app.register_blueprint(auth_routes.auth_bp)
        app.register_blueprint(main_routes.main_bp)

        # 创建数据库表
        db.create_all()

    return app
