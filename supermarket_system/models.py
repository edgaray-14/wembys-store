from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# Add Category model
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Category {self.name}>'

# Update Product to use a foreign key relationship to Category
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    price = db.Column(db.Numeric(12, 2), nullable=False)  # UGX
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    supplier = db.Column(db.String(150))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category.name if self.category else None,
            'price': float(self.price),
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'supplier': self.supplier,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True)
    quantity_on_hand = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    reorder_quantity = db.Column(db.Integer, default=50)
    last_restocked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_low_stock(self):
        """Check if stock is below reorder level."""
        return self.quantity_on_hand <= self.reorder_level
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity_on_hand': self.quantity_on_hand,
            'reorder_level': self.reorder_level,
            'reorder_quantity': self.reorder_quantity,
            'is_low_stock': self.is_low_stock(),
            'last_restocked': self.last_restocked.isoformat() if self.last_restocked else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transaction_type = db.Column(db.String(20), default='IN')  # IN, OUT, ADJUSTMENT, RETURN
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    reference_id = db.Column(db.String(100))  # Transaction ID, PO number, etc.
    created_by = db.Column(db.Integer)  # Employee ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'reason': self.reason,
            'reference_id': self.reference_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    customer_name = db.Column(db.String(150))
    cashier_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    status = db.Column(db.String(20), default='OPEN', nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    discount_type = db.Column(db.String(20), default='AMOUNT')
    discount_value = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    discount_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    tax_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    total_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    paid_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    change_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    payment_method = db.Column(db.String(20))
    promo_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('TransactionItem', backref='transaction', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='transaction', lazy=True, cascade='all, delete-orphan')

    def recalculate_totals(self, tax_rate):
        subtotal = sum(item.line_total for item in self.items)
        discount_amount = Decimal('0.00')
        if self.discount_type == 'PERCENT':
            discount_amount = (subtotal * Decimal(self.discount_value or 0) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            discount_amount = Decimal(self.discount_value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        taxable_amount = max(subtotal - discount_amount, Decimal('0.00'))
        tax_amount = (taxable_amount * Decimal(tax_rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount = (taxable_amount + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        self.subtotal = subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        return self.to_dict()

    def to_dict(self, include_items=True, include_payments=False):
        data = {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_name': self.customer_name,
            'cashier_id': self.cashier_id,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'discount_amount': float(self.discount_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'change_amount': float(self.change_amount),
            'payment_method': self.payment_method,
            'promo_code': self.promo_code,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        if include_payments:
            data['payments'] = [payment.to_dict() for payment in self.payments]
        return data


class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_type = db.Column(db.String(20), default='AMOUNT')
    discount_value = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    discount_amount = db.Column(db.Numeric(12, 2), default=Decimal('0.00'))
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')

    def calculate_line(self):
        raw_total = Decimal(self.unit_price) * Decimal(self.quantity)
        discount_amount = Decimal('0.00')
        if self.discount_type == 'PERCENT':
            discount_amount = (raw_total * Decimal(self.discount_value or 0) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            discount_amount = Decimal(self.discount_value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        self.discount_amount = min(discount_amount, raw_total)
        self.line_total = (raw_total - self.discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.line_total

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'sku': self.sku,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'discount_amount': float(self.discount_amount),
            'line_total': float(self.line_total),
            'created_at': self.created_at.isoformat()
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(100))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'method': self.method,
            'reference': self.reference,
            'paid_at': self.paid_at.isoformat()
        }


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.Text)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_permissions(self):
        try:
            return json.loads(self.permissions) if self.permissions else []
        except Exception:
            return []

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'permissions': self.get_permissions(), 'created_at': self.created_at.isoformat()}


class Employee(UserMixin, db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    phone = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = db.relationship('Role', backref='employees', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # UserMixin provides is_authenticated/is_active/is_anonymous/get_id
    def get_id(self):
        return str(self.id)

    def to_dict(self, include_role=False):
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_role and self.role:
            data['role'] = self.role.to_dict()
        else:
            data['role_id'] = self.role_id
        return data


class EmployeeAudit(db.Model):
    __tablename__ = 'employee_audit'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    action = db.Column(db.String(100))
    detail = db.Column(db.Text)
    ip = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'action': self.action,
            'detail': self.detail,
            'ip': self.ip,
            'created_at': self.created_at.isoformat()
        }
