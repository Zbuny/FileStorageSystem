from flask import Blueprint

files_bp = Blueprint('files', __name__, template_folder='templates', static_folder='static')

from . import views
