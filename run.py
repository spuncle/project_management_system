import os
from app import create_app, db
from app.models import User, Invitation

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Provides a shell context for 'flask shell' command."""
    return {'db': db, 'User': User, 'Invitation': Invitation}

if __name__ == '__main__':
    app.run(debug=True)
