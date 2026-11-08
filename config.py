import os

from flask_appbuilder.security.manager import AUTH_DB

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-no-usar-en-produccion")

# --- Base de datos MySQL ---------------------------------------------------
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "tienda_db")

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- Autenticación y seguridad --------------------------------------------
AUTH_TYPE = AUTH_DB
AUTH_USER_REGISTRATION = False  # solo el administrador crea usuarios
AUTH_ROLE_ADMIN = "Admin"
AUTH_ROLE_PUBLIC = "Public"  # sin permisos: obliga a iniciar sesión
WTF_CSRF_ENABLED = True

# --- Apariencia -----------------------------------------------------------
APP_NAME = "ELY - Tienda y Almacén "
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {"es": {"flag": "es", "name": "Español"}, "en": {"flag": "gb", "name": "English"}}

# --- Inteligencia artificial gratuita (Google Gemini) ---------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
