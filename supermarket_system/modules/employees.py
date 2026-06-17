from flask import Blueprint, request, jsonify, current_app
from models import db, Employee, Role, EmployeeAudit
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

def _record_audit(emp_id, action, detail='', ip=None):
    try:
        audit = EmployeeAudit(employee_id=emp_id, action=action, detail=detail, ip=ip)
        db.session.add(audit)
        db.session.commit()
    except Exception:
        db.session.rollback()

# Roles
@employees_bp.route('/roles', methods=['GET'])
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in roles]}), 200

@employees_bp.route('/roles', methods=['POST'])
def create_role():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    perms = data.get('permissions', [])
    if not name:
        return jsonify({'success': False, 'error': 'Role name required'}), 400
    role = Role(name=name, permissions=json.dumps(perms))
    try:
        db.session.add(role)
        db.session.commit()
        return jsonify({'success': True, 'data': role.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Role name already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Employee CRUD
@employees_bp.route('', methods=['GET'])
def list_employees():
    q = Employee.query.order_by(Employee.username)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    data = [e.to_dict(include_role=True) for e in pagination.items]
    return jsonify({'success': True, 'page': pagination.page, 'per_page': pagination.per_page, 'total': pagination.total, 'data': data}), 200

@employees_bp.route('', methods=['POST'])
def create_employee():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password')
    if not username or not password:
        return jsonify({'success': False, 'error': 'username and password required'}), 400
    if Employee.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'username already exists'}), 409
    emp = Employee(
        username=username,
        full_name=(data.get('full_name') or '').strip(),
        email=(data.get('email') or '').strip(),
        phone=(data.get('phone') or '').strip(),
        role_id=data.get('role_id'),
        is_active=bool(data.get('is_active', True))
    )
    emp.set_password(password)
    try:
        db.session.add(emp)
        db.session.commit()
        _record_audit(emp.id, 'CREATE', f'Employee {username} created')
        return jsonify({'success': True, 'data': emp.to_dict(include_role=True)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    emp = Employee.query.get(employee_id)
    if not emp:
        return jsonify({'success': False, 'error': 'Employee not found'}), 404
    data = request.get_json() or {}
    if 'full_name' in data: emp.full_name = (data.get('full_name') or '').strip()
    if 'email' in data: emp.email = (data.get('email') or '').strip()
    if 'phone' in data: emp.phone = (data.get('phone') or '').strip()
    if 'role_id' in data: emp.role_id = data.get('role_id')
    if 'is_active' in data: emp.is_active = bool(data.get('is_active'))
    if 'password' in data and data['password']:
        emp.set_password(data['password'])
    try:
        db.session.commit()
        _record_audit(emp.id, 'UPDATE', f'Employee {emp.username} updated')
        return jsonify({'success': True, 'data': emp.to_dict(include_role=True)}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Update conflict'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@employees_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    emp = Employee.query.get(employee_id)
    if not emp:
        return jsonify({'success': False, 'error': 'Employee not found'}), 404
    return jsonify({'success': True, 'data': emp.to_dict(include_role=True)}), 200

@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    emp = Employee.query.get(employee_id)
    if not emp:
        return jsonify({'success': False, 'error': 'Employee not found'}), 404
    try:
        emp.is_active = False
        db.session.commit()
        _record_audit(emp.id, 'DEACTIVATE', f'Employee {emp.username} deactivated')
        return jsonify({'success': True, 'message': 'Employee deactivated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Audit listing
@employees_bp.route('/audit', methods=['GET'])
def audit_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    q = EmployeeAudit.query.order_by(EmployeeAudit.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'success': True, 'page': pagination.page, 'per_page': pagination.per_page, 'total': pagination.total, 'data': [a.to_dict() for a in pagination.items]}), 200
