This repository contains the Festiv_Mart Django project (Seasonalapp).

Quick start (Windows PowerShell):

1. Activate virtualenv:

```powershell
cd "c:\Mern-full stack\capstone-project\Festiv_Mart"
.\festivenv\Scripts\Activate.ps1
```

2. Install dependencies (if needed):

```powershell
pip install -r requirements.txt
```

3. Run migrations and create superuser:

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

4. Run development server:

```powershell
python manage.py runserver
```

App URLs:
- `/` landing page
- `/products/` product list
- `/product/<slug>/` product detail
- `/signup/` sign up
- `/login/` login
- `/dashboard/` user dashboard (login required)

Notes:
- Templates are in `Seasonalapp/templates`.
- Database: default SQLite `db.sqlite3` in project root.
