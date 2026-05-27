# QA System — Tanzanian College

Flask-based Quality Assurance evaluation system with multi-campus support.

## Setup

### 1. Create and activate virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and fill in your values:
```
SECRET_KEY=your-random-secret-key
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/qa_system
```

### 4. Create PostgreSQL database
```sql
CREATE DATABASE qa_system;
```

### 5. Initialize and run migrations
```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

### 6. Seed with demo data
```bash
flask seed-db
```

### 7. Run the app
```bash
flask run
```

## Demo accounts

| Username  | Password     | Role             |
|-----------|-------------|------------------|
| admin     | admin123    | Head Admin       |
| qahead    | qa123       | QA Head Office   |
| admin1    | admin123    | Campus Admin     |
| qadar     | qa123       | QA Officer       |
| director1 | director123 | Campus Director  |
| ceo       | ceo123      | CEO              |
| jmushi    | lecturer123 | Lecturer         |
| student1  | student123  | Student          |
| student2  | student123  | Student          |

## Tech Stack
- Python / Flask 3.0
- PostgreSQL + SQLAlchemy + Flask-Migrate
- Bootstrap 5.3 + Font Awesome
- Plotly (interactive charts)
- ReportLab (PDF export)
- pandas + openpyxl (CSV/Excel export)
