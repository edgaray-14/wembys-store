from flask import Blueprint, request, jsonify
from models import db, Product, Category, Inventory

catalogue_bp = Blueprint('catalogue', __name__, url_prefix='/api/catalogue')

@catalogue_bp.route('/categories', methods=['GET'])
def categories():
    try:
        categories = Category.query.order_by(Category.name).all()
        return jsonify({'success': True, 'data': [cat.to_dict() for cat in categories]}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@catalogue_bp.route('/products', methods=['GET'])
def list_products():
    try:
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '', type=str).strip()
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        in_stock_only = request.args.get('in_stock', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 24, type=int)

        query = Product.query.filter(Product.is_visible == True, Product.is_active == True)

        if category_id:
            query = query.filter_by(category_id=category_id)

        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                    Product.barcode.ilike(search_pattern)
                )
            )

        if min_price is not None:
            query = query.filter(Product.unit_price >= min_price)
        if max_price is not None:
            query = query.filter(Product.unit_price <= max_price)

        if in_stock_only:
            query = query.join(Inventory).filter(Inventory.quantity_on_hand > 0)

        pagination = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)
        items = [product.to_dict(include_inventory=True) for product in pagination.items]

        return jsonify({
            'success': True,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'data': items
        }), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@catalogue_bp.route('/products/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    try:
        product = Product.query.filter_by(id=product_id, is_visible=True, is_active=True).first()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        return jsonify({'success': True, 'data': product.to_dict(include_inventory=True)}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500
