import json
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.template_filter('from_json')
    def from_json_filter(s):
        return json.loads(s) if s else []

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.evaluation import bp as eval_bp
    app.register_blueprint(eval_bp, url_prefix='/evaluation')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.forms_manager import bp as forms_bp
    app.register_blueprint(forms_bp, url_prefix='/forms')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from flask_login import current_user
    from datetime import datetime, timezone

    @app.before_request
    def update_last_active():
        if current_user.is_authenticated:
            current_user.last_active = datetime.now(timezone.utc).replace(tzinfo=None)
            db.session.commit()

    # ── CLI commands ──────────────────────────────────────────────────────────

    @app.cli.command('seed-db')
    def seed_db_command():
        """Seed the database with initial demo data."""
        import sys
        import os
        # seed_data.py lives at the project root (one level up from app/)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from seed_data import seed
        seed()
        click.echo('seed-db done.')

    @app.cli.command('seed-templates')
    def seed_templates_command():
        """Seed the standard evaluation form templates."""
        from app.utils.template_seeder import seed_templates
        created, skipped = seed_templates()
        click.echo(f'seed-templates done: {created} created, {skipped} skipped.')

    # ─────────────────────────────────────────────────────────────────────────

    return app
