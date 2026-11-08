import logging

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA

from .index import ElyIndexView

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
appbuilder = AppBuilder(app, db.session, indexview=ElyIndexView)

# Se importan al final para evitar importaciones circulares
from . import models  # noqa: E402,F401
from . import views  # noqa: E402,F401
from . import reportes  # noqa: E402,F401
from . import asistente  # noqa: E402,F401
