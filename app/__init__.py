import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = '请先登录以访问此页面。'

def create_app(template_folder=None, static_folder=None):
    app = Flask(__name__,
                instance_relative_config=True,
                template_folder=template_folder,
                static_folder=static_folder)

    app.config.from_pyfile('config.py', silent=True)
    
    bootstrap = Bootstrap5(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    CSRFProtect(app)
    
    with app.app_context():
        from .auth import routes as auth_routes
        from .main import routes as main_routes
        from .admin import routes as admin_routes # <--- 1. 导入 admin 路由

        app.register_blueprint(auth_routes.auth_bp)
        app.register_blueprint(main_routes.main_bp)
        app.register_blueprint(admin_routes.admin_bp) # <--- 2. 注册 admin 蓝图

        db.create_all()

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

    return app