from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Employee
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    # Accept form or JSON
    data = request.get_json() or request.form
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'success': False, 'error': 'username and password required'}), 400

    user = Employee.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'error': 'account disabled'}), 403

    login_user(user)
    return jsonify({'success': True, 'data': user.to_dict(include_role=True)}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'logged out'}), 200

@auth_bp.route('/me', methods=['GET'])
def me():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': current_user.to_dict(include_role=True)}), 200
    return jsonify({'authenticated': False}), 200