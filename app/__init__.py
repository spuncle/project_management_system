import os
from flask import Flask, render_template, request, jsonify # 导入 request 和 jsonify
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

def create_app():
    # ... (上半部分硬编码路径的代码无变化) ...
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(APP_DIR, 'templates')
    STATIC_DIR = os.path.join(APP_DIR, 'static')

    app = Flask(__name__,
                instance_relative_config=True,
                template_folder=TEMPLATE_DIR,
                static_folder=STATIC_DIR)

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

        # vvv --- 更新 403 错误处理器 --- vvv
        @app.errorhandler(403)
        def forbidden_error(error):
            # 如果是API请求 (通常接受JSON)，则返回JSON错误信息
            if request.accept_mimetypes.accept_json and \
                    not request.accept_mimetypes.accept_html:
                return jsonify({'success': False, 'error': '权限不足，无法执行此操作。'}), 403
            # 否则，为普通页面访问渲染403模板
            return render_template('403.html'), 403
        # ^^^ --------------------------- ^^^

        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

    return app