from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()  # 이 명령은 프로젝트 루트에 있는 .env 파일을 로드합니다.

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.getenv("SECRET_KEY")

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
