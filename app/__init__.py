import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
    )

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
