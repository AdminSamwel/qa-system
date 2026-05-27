import os
import click
from app import create_app, db
from app.models import User, Campus, Department, Programme

app = create_app()


@app.cli.command('init-db')
def init_db():
    """Create all database tables."""
    db.create_all()
    click.echo('Database tables created.')


@app.cli.command('seed-db')
def seed_db():
    """Seed the database with initial data."""
    from seed_data import seed
    seed()
    click.echo('Database seeded.')


@app.cli.command('seed-templates')
def seed_templates_cmd():
    """Seed the two standard evaluation form templates (NACTVET + TPSC QA)."""
    from app.utils.template_seeder import seed_templates
    created, skipped = seed_templates()
    click.echo(f'Templates: {created} created, {skipped} skipped (already exist).')


if __name__ == '__main__':
    app.run(debug=True)
