from flask import Blueprint
bp = Blueprint('evaluation', __name__)
from app.evaluation import routes