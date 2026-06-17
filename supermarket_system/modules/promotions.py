from flask import Blueprint, request, jsonify
from models import db
from datetime import datetime
from decimal import Decimal

promotions_bp = Blueprint('promotions', __name__, url_prefix='/api/promotions')

class Promotion(db.Model):
    __tablename__ = 'promotions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20), default='PERCENT')  # PERCENT or AMOUNT
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    min_purchase = db.Column(db.Numeric(10, 2), default=0)
    max_discount = db.Column(db.Numeric(10, 2))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'min_purchase': float(self.min_purchase),
            'max_discount': float(self.max_discount) if self.max_discount else None,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@promotions_bp.route('', methods=['GET'])
def list_promotions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    q = Promotion.query.order_by(Promotion.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'success': True,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'data': [p.to_dict() for p in pagination.items]
    }), 200

@promotions_bp.route('', methods=['POST'])
def create_promotion():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'name required'}), 400

    try:
        promo = Promotion(
            name=name,
            description=(data.get('description') or '').strip(),
            discount_type=data.get('discount_type', 'PERCENT'),
            discount_value=Decimal(str(data.get('discount_value', 0))),
            min_purchase=Decimal(str(data.get('min_purchase', 0))),
            max_discount=Decimal(str(data.get('max_discount'))) if data.get('max_discount') else None,
            start_date=datetime.fromisoformat(data.get('start_date')),
            end_date=datetime.fromisoformat(data.get('end_date')),
            is_active=bool(data.get('is_active', True))
        )
        db.session.add(promo)
        db.session.commit()
        return jsonify({'success': True, 'data': promo.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@promotions_bp.route('/<int:promo_id>', methods=['GET'])
def get_promotion(promo_id):
    promo = Promotion.query.get(promo_id)
    if not promo:
        return jsonify({'success': False, 'error': 'Promotion not found'}), 404
    return jsonify({'success': True, 'data': promo.to_dict()}), 200

@promotions_bp.route('/<int:promo_id>', methods=['PUT'])
def update_promotion(promo_id):
    promo = Promotion.query.get(promo_id)
    if not promo:
        return jsonify({'success': False, 'error': 'Promotion not found'}), 404

    data = request.get_json() or {}
    try:
        if 'name' in data: promo.name = (data.get('name') or '').strip()
        if 'description' in data: promo.description = (data.get('description') or '').strip()
        if 'discount_type' in data: promo.discount_type = data.get('discount_type')
        if 'discount_value' in data: promo.discount_value = Decimal(str(data.get('discount_value')))
        if 'min_purchase' in data: promo.min_purchase = Decimal(str(data.get('min_purchase')))
        if 'max_discount' in data: promo.max_discount = Decimal(str(data.get('max_discount'))) if data.get('max_discount') else None
        if 'start_date' in data: promo.start_date = datetime.fromisoformat(data.get('start_date'))
        if 'end_date' in data: promo.end_date = datetime.fromisoformat(data.get('end_date'))
        if 'is_active' in data: promo.is_active = bool(data.get('is_active'))

        db.session.commit()
        return jsonify({'success': True, 'data': promo.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@promotions_bp.route('/<int:promo_id>', methods=['DELETE'])
def delete_promotion(promo_id):
    promo = Promotion.query.get(promo_id)
    if not promo:
        return jsonify({'success': False, 'error': 'Promotion not found'}), 404
    try:
        promo.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Promotion deactivated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
