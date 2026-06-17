from flask import Blueprint, request, jsonify
from models import db, Product
from datetime import datetime
from decimal import Decimal

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@inventory_bp.route('/products', methods=['GET'])
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    category = request.args.get('category', None)
    search = request.args.get('search', None)

    query = Product.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'success': True,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'data': [p.to_dict() for p in pagination.items]
    }), 200

@inventory_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Product.category).distinct().all()
    return jsonify({
        'success': True,
        'data': [c[0] for c in categories if c[0]]
    }), 200

@inventory_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    sku = (data.get('sku') or '').strip()
    
    if not name or not sku:
        return jsonify({'success': False, 'error': 'name and sku required'}), 400

    if Product.query.filter_by(sku=sku).first():
        return jsonify({'success': False, 'error': 'SKU already exists'}), 400

    try:
        product = Product(
            name=name,
            sku=sku,
            category=(data.get('category') or '').strip(),
            price=Decimal(str(data.get('price', 0))),
            quantity=int(data.get('quantity', 0)),
            min_stock=int(data.get('min_stock', 10)),
            supplier=(data.get('supplier') or '').strip(),
            description=(data.get('description') or '').strip(),
            is_active=bool(data.get('is_active', True))
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'data': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    return jsonify({'success': True, 'data': product.to_dict()}), 200

@inventory_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    data = request.get_json() or {}
    try:
        if 'name' in data: product.name = (data.get('name') or '').strip()
        if 'sku' in data: 
            sku = (data.get('sku') or '').strip()
            if sku != product.sku and Product.query.filter_by(sku=sku).first():
                return jsonify({'success': False, 'error': 'SKU already exists'}), 400
            product.sku = sku
        if 'category' in data: product.category = (data.get('category') or '').strip()
        if 'price' in data: product.price = Decimal(str(data.get('price')))
        if 'quantity' in data: product.quantity = int(data.get('quantity'))
        if 'min_stock' in data: product.min_stock = int(data.get('min_stock'))
        if 'supplier' in data: product.supplier = (data.get('supplier') or '').strip()
        if 'description' in data: product.description = (data.get('description') or '').strip()
        if 'is_active' in data: product.is_active = bool(data.get('is_active'))

        db.session.commit()
        return jsonify({'success': True, 'data': product.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    try:
        product.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deactivated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
