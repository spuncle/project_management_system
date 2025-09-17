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

def create_app(): # 注意：我们移除了函数签名中的参数
    # --- 新增代码：明确定义绝对路径 ---
    import os
    # __file__ 指向当前文件 (app/__init__.py)
    # os.path.dirname() 获取该文件所在的目录 (app/)
    # os.path.abspath() 获取其绝对路径
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(APP_DIR, 'templates')
    STATIC_DIR = os.path.join(APP_DIR, 'static')

    app = Flask(__name__,
                instance_relative_config=True,
                template_folder=TEMPLATE_DIR, # <--- 强制使用绝对路径
                static_folder=STATIC_DIR)     # <--- 静态文件夹也一并强制指定

    # ------------------------------------

    # 后面的配置和初始化代码保持不变
    app.config.from_pyfile('config.py', silent=True)

    bootstrap = Bootstrap5(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    CSRFProtect(app)

    with app.app_context():
        from .auth import routes as auth_routes
        from .main import routes as main_routes
        from .admin import routes as admin_routes

        app.register_blueprint(auth_routes.auth_bp)
        app.register_blueprint(main_routes.main_bp)
        app.register_blueprint(admin_routes.admin_bp)

        db.create_all()

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

    return app
