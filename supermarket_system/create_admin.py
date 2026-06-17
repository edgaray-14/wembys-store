import argparse
from getpass import getpass

from app import app
from models import db, Employee, Role

def create_admin(username, password, full_name=None, email=None, role_name='admin'):
    with app.app_context():
        existing = Employee.query.filter_by(username=username).first()
        if existing:
            print(f'User "{username}" already exists.')
            return

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, permissions='["admin"]')
            db.session.add(role)
            db.session.flush()

        employee = Employee(
            username=username,
            full_name=full_name,
            email=email,
            role_id=role.id,
            is_active=True
        )
        employee.set_password(password)
        db.session.add(employee)
        db.session.commit()
        print(f'Admin user "{username}" created successfully.')

def main():
    parser = argparse.ArgumentParser(description='Create initial supermarket admin user')
    parser.add_argument('--username', required=True, help='Admin username')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--full-name', help='Full name')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--role', default='admin', help='Role name (default: admin)')
    args = parser.parse_args()

    password = args.password or getpass('Password: ')
    if not password:
        raise SystemExit('Password is required.')

    create_admin(
        username=args.username,
        password=password,
        full_name=args.full_name,
        email=args.email,
        role_name=args.role
    )

if __name__ == '__main__':
    main()