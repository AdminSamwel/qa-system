from flask import Blueprint
bp = Blueprint('forms_manager', __name__)
from app.forms_manager import routes