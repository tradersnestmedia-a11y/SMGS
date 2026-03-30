# Sim Tech Academy School Management System

This is a beginner-friendly Django school management system for **Sim Tech Academy**.

## Features

- Role-based login for Admin, Teacher, and Student users
- Student and staff self-registration with admin approval workflow
- Student management with create, update, delete, list, and profile pages
- Teacher management with create, update, delete, list, and profile pages
- Class and subject management
- Teacher-to-class and teacher-to-subject assignments
- Attendance marking per class and date
- Grade upload for teachers
- Result viewing for students
- Admin dashboard with simple statistics
- Responsive Bootstrap interface inspired by the provided screenshots

## Tech Stack

- Python
- Django
- SQLite
- Bootstrap 5

## Project Structure

- `simtech_academy/` - Django project settings and root URLs
- `accounts/` - login, logout, dashboard, role handling
- `students/` - student records and views
- `teachers/` - teacher records and views
- `academics/` - classes, subjects, assignments, attendance, grades
- `templates/` - shared and app templates
- `static/` - custom CSS

## How to Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Optional but recommended: set the Gmail app password for real email delivery:

Windows PowerShell:

```powershell
$env:SIMTECH_EMAIL_PASSWORD="your-gmail-app-password"
```

If this is not set, the system uses Django's console email backend for development.

3. Create migrations if needed:

```bash
python manage.py makemigrations
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Load sample data:

```bash
python manage.py seed_school
```

6. Start the development server:

```bash
python manage.py runserver
```

7. Open your browser:

```text
http://127.0.0.1:8000/
```

## Demo Logins

- Admin: `admin` / `admin12345`
- Teacher: `mchola` / `teacher12345`
- Student: `sianthony` / `student12345`

## Notes

- SQLite is used by default, so no extra database setup is required.
- Real email notifications are configured to use `tradersnestmedia@gmail.com`.
- SMS notifications use a console/logging fallback by default until a live Zambian SMS gateway is configured.
- Registration credentials are only generated and sent after admin approval.
- You can also create your own admin account with:

```bash
python manage.py createsuperuser
```

- A single-file code bundle is generated in `COMPLETE_PROJECT_CODE.md`.
