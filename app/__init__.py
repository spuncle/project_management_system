import os
from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # <--- 1. 导入 Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate() # <--- 2. 创建 Migrate 实例

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = '请先登录以访问此页面。'

def create_app():
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(APP_DIR, 'templates')
    STATIC_DIR = os.path.join(APP_DIR, 'static')

    app = Flask(__name__,
                instance_relative_config=True,
                template_folder=TEMPLATE_DIR,
                static_folder=STATIC_DIR)

    app.config.from_pyfile('config.py', silent=True)
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    
    bootstrap = Bootstrap5(app)
    db.init_app(app)
    migrate.init_app(app, db) # <--- 3. 初始化 Migrate
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

        # 我们不再需要 db.create_all() 和自动设置管理员的逻辑
        # from .models import User
        # if User.query.count() == 1: ...

        @app.errorhandler(403)
        def forbidden_error(error):
            if request.accept_mimetypes.accept_json and \
                    not request.accept_mimetypes.accept_html:
                return jsonify({'success': False, 'error': '权限不足，无法执行此操作。'}), 403
            return render_template('403.html'), 403

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

    return app