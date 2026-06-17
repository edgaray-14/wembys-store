# WEMBY'S STORE

A supermarket management system built with Python, Flask, MySQL, and Bootstrap.

## Project Overview

WEMBY'S STORE is a small supermarket web application designed to manage:
- inventory and product catalogue
- billing and transactions
- employees and user roles
- promotions
- a modern branded UI with a supermarket aesthetic

The project uses Flask for the backend, SQLAlchemy for ORM, MySQL for persistence, and Bootstrap + custom CSS for the frontend.

## Key Features

- authenticated admin/employee flows
- inventory page with product search, filtering, and CRUD
- product catalogue with UGX pricing
- employee management with roles
- promotions page
- responsive UI with custom branding
- background image and themed design

## Tech Stack

- Python 3.x
- Flask
- Flask-Login
- Flask-SQLAlchemy
- PyMySQL
- Bootstrap 5
- JavaScript / Fetch API
- MySQL (via XAMPP or standalone)
- HTML / CSS

## How It Was Built

- `app.py` initializes Flask, registers blueprints, and connects to the database.
- `models.py` defines database tables using SQLAlchemy.
- `modules/` contains separate blueprint modules for each domain:
  - `auth`
  - `inventory`
  - `billing`
  - `catalogue`
  - `employees`
  - `promotions`
- `templates/` holds Jinja2 HTML templates for the web pages.
- `static/css/style.css` defines the WEMBY’S STORE theme, colors, and background.
- `static/js/` contains frontend logic for inventory, promotions, and UI interaction.
- `static/images/` stores the supermarket background image.

## Installation

1. Clone or download the repository:
   ```bash
   cd C:\Users\hp\Downloads\Billing-Invoice-GUI-main
   ```

2. Create and activate the virtual environment:
   ```powershell
   python -m venv .venv
   & ".\.venv\Scripts\Activate.ps1"
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure MySQL:
   - Start XAMPP and enable MySQL.
   - Create the database:
     ```powershell
     & 'C:\xampp\mysql\bin\mysql.exe' -u root -e "CREATE DATABASE supermarket CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
     ```
   - If root uses a password, add `-p`.

5. Set environment variables if needed:
   - `DATABASE_URL`
   - `FLASK_ENV=development`

## Running the App

```powershell
cd "C:\Users\hp\Downloads\Billing-Invoice-GUI-main"
& ".\.venv\Scripts\python.exe" ".\supermarket_system\app.py"
```

Then open:
```
http://127.0.0.1:5000
```

## Database Notes

- The app expects a MySQL database named `supermarket`.
- The schema is created automatically on startup with `db.create_all()`.
- Product seeding can populate initial inventory items automatically.

## Project Structure

- `supermarket_system/app.py` — main Flask application
- `supermarket_system/config.py` — configuration settings
- `supermarket_system/models.py` — SQLAlchemy ORM models
- `supermarket_system/modules/` — Blueprint modules
- `supermarket_system/templates/` — HTML templates
- `supermarket_system/static/` — CSS, JS, images
- `supermarket_system/static/images/` — supermarket background image

## Customization

- Change the project title in `templates/base.html`
- Update colors and background in `static/css/style.css`
- Add or edit product seed data in `app.py` or `modules/inventory.py`
- Add roles and employee logic in `models.py` and `modules/employees.py`

## Contact

For email/contact display in the app:
- `wembystore14@gmail.com`

---

This README gives a complete project summary, installation steps, and technology stack for WEMBY’S STORE.
