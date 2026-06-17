from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime

from models import db, Product, Inventory, InventoryTransaction, Transaction, TransactionItem, Payment

billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

def _make_invoice_number():
    prefix = 'INV'
    now = datetime.utcnow()
    suffix = now.strftime('%Y%m%d%H%M%S')
    return f'{prefix}{suffix}'

def _get_open_transaction(transaction_id):
    tx = Transaction.query.filter_by(id=transaction_id, status='OPEN').first()
    return tx

def _validate_payment_method(method):
    return method in ['CASH', 'CARD', 'MOBILE_MONEY']

@billing_bp.route('/carts', methods=['POST'])
@login_required
def create_cart():
    data = request.get_json() or {}
    invoice_number = _make_invoice_number()
    # Use logged-in employee as cashier
    cashier_id = current_user.id if current_user.is_authenticated else data.get('cashier_id')
    cart = Transaction(
        invoice_number=invoice_number,
        customer_name=data.get('customer_name'),
        cashier_id=cashier_id,
        discount_type=data.get('discount_type', 'AMOUNT'),
        discount_value=Decimal(str(data.get('discount_value', '0.00')))
    )
    db.session.add(cart)
    db.session.commit()
    return jsonify({'success': True, 'data': cart.to_dict(include_items=True)}), 201

@billing_bp.route('/carts/<int:cart_id>', methods=['GET'])
def get_cart(cart_id):
    cart = _get_open_transaction(cart_id)
    if not cart:
        return jsonify({'success': False, 'error': 'Cart not found or already completed'}), 404
    cart.recalculate_totals(current_app.config['TAX_RATE'])
    return jsonify({'success': True, 'data': cart.to_dict(include_items=True)}), 200

@billing_bp.route('/carts/<int:cart_id>/items', methods=['POST'])
def add_item_to_cart(cart_id):
    cart = _get_open_transaction(cart_id)
    if not cart:
        return jsonify({'success': False, 'error': 'Cart not found or already completed'}), 404

    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    discount_type = data.get('discount_type', 'AMOUNT')
    discount_value = Decimal(str(data.get('discount_value', '0.00')))

    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID is required'}), 400
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Quantity must be an integer'}), 400
    if quantity <= 0:
        return jsonify({'success': False, 'error': 'Quantity must be greater than zero'}), 400

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'success': False, 'error': 'Product not found or inactive'}), 404

    inventory = Inventory.query.filter_by(product_id=product_id).first()
    if inventory and inventory.quantity_on_hand < quantity:
        return jsonify({
            'success': False,
            'error': 'Insufficient stock for this item',
            'available_quantity': inventory.quantity_on_hand
        }), 400

    existing_item = TransactionItem.query.filter_by(transaction_id=cart.id, product_id=product_id).first()
    if existing_item:
        existing_item.quantity += quantity
        existing_item.discount_type = discount_type
        existing_item.discount_value = discount_value
        existing_item.calculate_line()
    else:
        item = TransactionItem(
            transaction_id=cart.id,
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            quantity=quantity,
            unit_price=product.unit_price,
            discount_type=discount_type,
            discount_value=discount_value
        )
        item.calculate_line()
        db.session.add(item)

    cart.recalculate_totals(current_app.config['TAX_RATE'])
    db.session.commit()
    return jsonify({'success': True, 'data': cart.to_dict(include_items=True)}), 201

@billing_bp.route('/carts/<int:cart_id>/items/<int:item_id>', methods=['PUT'])
def update_cart_item(cart_id, item_id):
    cart = _get_open_transaction(cart_id)
    if not cart:
        return jsonify({'success': False, 'error': 'Cart not found or already completed'}), 404

    item = TransactionItem.query.filter_by(id=item_id, transaction_id=cart.id).first()
    if not item:
        return jsonify({'success': False, 'error': 'Cart item not found'}), 404

    data = request.get_json() or {}
    if 'quantity' in data:
        try:
            quantity = int(data['quantity'])
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Quantity must be an integer'}), 400
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than zero'}), 400

        inventory = Inventory.query.filter_by(product_id=item.product_id).first()
        if inventory and inventory.quantity_on_hand < quantity:
            return jsonify({
                'success': False,
                'error': 'Insufficient stock for this item',
                'available_quantity': inventory.quantity_on_hand
            }), 400
        item.quantity = quantity

    if 'discount_type' in data:
        item.discount_type = data['discount_type']
    if 'discount_value' in data:
        item.discount_value = Decimal(str(data['discount_value'] or '0.00'))

    item.calculate_line()
    cart.recalculate_totals(current_app.config['TAX_RATE'])
    db.session.commit()
    return jsonify({'success': True, 'data': cart.to_dict(include_items=True)}), 200

@billing_bp.route('/carts/<int:cart_id>/items/<int:item_id>', methods=['DELETE'])
def remove_cart_item(cart_id, item_id):
    cart = _get_open_transaction(cart_id)
    if not cart:
        return jsonify({'success': False, 'error': 'Cart not found or already completed'}), 404

    item = TransactionItem.query.filter_by(id=item_id, transaction_id=cart.id).first()
    if not item:
        return jsonify({'success': False, 'error': 'Cart item not found'}), 404

    db.session.delete(item)
    cart.recalculate_totals(current_app.config['TAX_RATE'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item removed', 'data': cart.to_dict(include_items=True)}), 200

@billing_bp.route('/carts/<int:cart_id>/checkout', methods=['POST'])
@login_required
def checkout(cart_id):
    cart = _get_open_transaction(cart_id)
    if not cart:
        return jsonify({'success': False, 'error': 'Cart not found or already completed'}), 404

    if not cart.items:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    data = request.get_json() or {}
    payment_method = data.get('payment_method')
    paid_amount = data.get('paid_amount')
    reference = data.get('reference')

    if not payment_method or not _validate_payment_method(payment_method):
        return jsonify({'success': False, 'error': 'Valid payment method required'}), 400

    try:
        paid_amount = Decimal(str(paid_amount))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Paid amount must be a number'}), 400

    cart.recalculate_totals(current_app.config['TAX_RATE'])
    if paid_amount < cart.total_amount:
        return jsonify({'success': False, 'error': 'Paid amount is less than total due'}), 400

    # Verify inventory before finalizing
    for item in cart.items:
        inventory = Inventory.query.filter_by(product_id=item.product_id).first()
        if inventory and inventory.quantity_on_hand < item.quantity:
            return jsonify({
                'success': False,
                'error': f'Insufficient stock for {item.product_name}',
                'available_quantity': inventory.quantity_on_hand
            }), 400

    cart.payment_method = payment_method
    cart.paid_amount = paid_amount
    cart.change_amount = (paid_amount - cart.total_amount).quantize(Decimal('0.01'))
    cart.status = 'COMPLETED'

    payment = Payment(
        transaction_id=cart.id,
        amount=paid_amount,
        method=payment_method,
        reference=reference
    )
    db.session.add(payment)

    # Deduct inventory and record stock out
    for item in cart.items:
        inventory = Inventory.query.filter_by(product_id=item.product_id).first()
        if inventory:
            inventory.quantity_on_hand -= item.quantity
            inventory.last_restocked = datetime.utcnow()
            db.session.add(InventoryTransaction(
                product_id=item.product_id,
                transaction_type='OUT',
                quantity=item.quantity,
                reason=f'Sale {cart.invoice_number}',
                reference_id=cart.invoice_number,
                created_by=cart.cashier_id
            ))

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Checkout completed successfully',
        'data': cart.to_dict(include_items=True, include_payments=True)
    }), 200

@billing_bp.route('/transactions', methods=['GET'])
def transaction_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Transaction.query
    if status:
        query = query.filter_by(status=status.upper())
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)

    pagination = query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = [tx.to_dict(include_items=False, include_payments=False) for tx in pagination.items]

    return jsonify({
        'success': True,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'data': items
    }), 200

@billing_bp.route('/transactions/daily-summary', methods=['GET'])
def daily_summary():
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.utcnow().strftime('%Y-%m-%d')

    summary_query = db.session.query(
        db.func.count(Transaction.id),
        db.func.sum(Transaction.total_amount),
        db.func.sum(Transaction.paid_amount)
    ).filter(
        db.func.date(Transaction.created_at) == date_str,
        Transaction.status == 'COMPLETED'
    ).first()

    return jsonify({
        'success': True,
        'date': date_str,
        'total_sales': int(summary_query[0] or 0),
        'total_revenue': float(summary_query[1] or 0),
        'total_collected': float(summary_query[2] or 0)
    }), 200

@billing_bp.route('/transactions/<int:transaction_id>/receipt', methods=['GET'])
def transaction_receipt(transaction_id):
    tx = Transaction.query.get(transaction_id)
    if not tx:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    return render_template('receipt.html', transaction=tx)
