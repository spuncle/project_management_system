import os
from app import create_app, db
from app.models import User, InvitationCode 

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """为 'flask shell' 命令提供上下文。"""
    return {'db': db, 'User': User, 'InvitationCode': InvitationCode}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)