from flask import Flask, render_template
from config import Config
from models import db, Role, Product, Category
from modules.inventory import inventory_bp
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Initialize Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

from models import Employee  # ensure import for user loader

@login_manager.user_loader
def load_user(user_id):
    try:
        return Employee.query.get(int(user_id))
    except Exception:
        return None

@app.before_request
def seed_roles():
    from models import Role
    if Role.query.count() < 4:
        roles_to_add = [
            Role(name='admin', permissions='["admin"]'),
            Role(name='cashier', permissions='["cashier"]'),
            Role(name='manager', permissions='["manage_employees"]'),
            Role(name='attendant', permissions='["attendant"]'),
            Role(name='storemanager', permissions='["storemanager"]'),
        ]
        for role in roles_to_add:
            if not Role.query.filter_by(name=role.name).first():
                db.session.add(role)
        db.session.commit()

@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        seed_products()

# Register blueprints (existing + auth)
from modules.auth import auth_bp
from modules.inventory import inventory_bp
from modules.billing import billing_bp
from modules.catalogue import catalogue_bp
from modules.employees import employees_bp
from modules.promotions import promotions_bp

app.register_blueprint(auth_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(catalogue_bp)
app.register_blueprint(employees_bp)
app.register_blueprint(promotions_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    return render_template('inventory.html')

# Seed products on startup
def seed_products():
    if Product.query.count() > 0:
        return

    products = [
        # (sku, name, category, price, supplier)  -- use your existing list
        ('RICE001', 'Uganda Rice 1kg', 'Grains & Cereals', 8000, 'Grain Supplier Co'),
        ('RICE002', 'Basmati Rice 2kg', 'Grains & Cereals', 15000, 'Grain Supplier Co'),
        ('RICE003', 'Brown Rice 1kg', 'Grains & Cereals', 6500, 'Grain Supplier Co'),
        ('WHEAT001', 'Wheat Flour 2kg', 'Grains & Cereals', 7500, 'Grain Supplier Co'),
        ('WHEAT002', 'Self Raising Flour 2kg', 'Grains & Cereals', 8000, 'Grain Supplier Co'),
        ('CORN001', 'Corn Meal 2kg', 'Grains & Cereals', 5500, 'Grain Supplier Co'),
        ('OAT001', 'Oat Cereal 500g', 'Grains & Cereals', 6000, 'Grain Supplier Co'),
        ('MILLET001', 'Millet Flour 1kg', 'Grains & Cereals', 4500, 'Grain Supplier Co'),
        ('PASTA001', 'Pasta Spaghetti 500g', 'Grains & Cereals', 3500, 'Grain Supplier Co'),
        ('PASTA002', 'Pasta Penne 500g', 'Grains & Cereals', 3500, 'Grain Supplier Co'),
        ('BREAD001', 'White Bread 600g', 'Grains & Cereals', 2500, 'Local Bakery'),
        ('BREAD002', 'Brown Bread 600g', 'Grains & Cereals', 3000, 'Local Bakery'),
        ('CEREAL001', 'Corn Flakes 250g', 'Grains & Cereals', 4500, 'Grain Supplier Co'),
        ('CEREAL002', 'Wheat Bran 500g', 'Grains & Cereals', 3000, 'Grain Supplier Co'),
        ('BEANS001', 'Dry Beans 1kg', 'Grains & Cereals', 4000, 'Grain Supplier Co'),
        ('BEANS002', 'Lentils 1kg', 'Grains & Cereals', 5500, 'Grain Supplier Co'),
        ('PEA001', 'Split Peas 1kg', 'Grains & Cereals', 4500, 'Grain Supplier Co'),
        ('GROUNDNUT001', 'Groundnuts 500g', 'Grains & Cereals', 6000, 'Grain Supplier Co'),
        ('SESAME001', 'Sesame Seeds 250g', 'Grains & Cereals', 5500, 'Grain Supplier Co'),
        ('SUNFLOWER001', 'Sunflower Seeds 500g', 'Grains & Cereals', 4500, 'Grain Supplier Co'),
        
        # Oils & Fats (15 items)
        ('OIL001', 'Palm Oil 1L', 'Oils & Fats', 5500, 'Oil Traders Ltd'),
        ('OIL002', 'Sunflower Oil 1L', 'Oils & Fats', 8500, 'Oil Traders Ltd'),
        ('OIL003', 'Coconut Oil 500ml', 'Oils & Fats', 7000, 'Oil Traders Ltd'),
        ('OIL004', 'Olive Oil 500ml', 'Oils & Fats', 12000, 'Oil Traders Ltd'),
        ('OIL005', 'Groundnut Oil 1L', 'Oils & Fats', 9000, 'Oil Traders Ltd'),
        ('BUTTER001', 'Butter 250g', 'Oils & Fats', 8000, 'Dairy Co'),
        ('BUTTER002', 'Margarine 500g', 'Oils & Fats', 5500, 'Dairy Co'),
        ('GHEE001', 'Ghee 500ml', 'Oils & Fats', 12000, 'Dairy Co'),
        ('SHORTENING001', 'Vegetable Shortening 500g', 'Oils & Fats', 6500, 'Oil Traders Ltd'),
        ('LARD001', 'Lard 500g', 'Oils & Fats', 7500, 'Oil Traders Ltd'),
        ('COOKING_SPRAY001', 'Cooking Spray 300ml', 'Oils & Fats', 4500, 'Oil Traders Ltd'),
        ('MAYONNAISE001', 'Mayonnaise 500ml', 'Oils & Fats', 7000, 'Condiment Co'),
        ('PEANUT_BUTTER001', 'Peanut Butter 500g', 'Oils & Fats', 8500, 'Nut Traders'),
        ('SESAME_OIL001', 'Sesame Oil 250ml', 'Oils & Fats', 9500, 'Oil Traders Ltd'),
        ('FISH_OIL001', 'Fish Oil 500ml', 'Oils & Fats', 15000, 'Oil Traders Ltd'),
        
        # Beverages (20 items)
        ('TEA001', 'Black Tea 500g', 'Beverages', 6000, 'Tea Estates'),
        ('TEA002', 'Green Tea 250g', 'Beverages', 7500, 'Tea Estates'),
        ('COFFEE001', 'Instant Coffee 200g', 'Beverages', 9000, 'Coffee Roasters'),
        ('COFFEE002', 'Ground Coffee 500g', 'Beverages', 12000, 'Coffee Roasters'),
        ('COFFEE003', 'Coffee Beans 250g', 'Beverages', 10000, 'Coffee Roasters'),
        ('COCOA001', 'Cocoa Powder 500g', 'Beverages', 8000, 'Cocoa Suppliers'),
        ('COCOA002', 'Hot Chocolate 200g', 'Beverages', 6500, 'Cocoa Suppliers'),
        ('JUICE001', 'Orange Juice 1L', 'Beverages', 4500, 'Juice Makers'),
        ('JUICE002', 'Mango Juice 1L', 'Beverages', 4500, 'Juice Makers'),
        ('JUICE003', 'Passion Fruit Juice 1L', 'Beverages', 5000, 'Juice Makers'),
        ('JUICE004', 'Pineapple Juice 1L', 'Beverages', 4500, 'Juice Makers'),
        ('SODA001', 'Cola 1.5L', 'Beverages', 3500, 'Beverage Co'),
        ('SODA002', 'Fanta Orange 1.5L', 'Beverages', 3500, 'Beverage Co'),
        ('SODA003', 'Sprite 1.5L', 'Beverages', 3500, 'Beverage Co'),
        ('WATER001', 'Bottled Water 500ml', 'Beverages', 1500, 'Water Co'),
        ('WATER002', 'Bottled Water 1.5L', 'Beverages', 2500, 'Water Co'),
        ('ENERGY001', 'Energy Drink 250ml', 'Beverages', 3500, 'Beverage Co'),
        ('MILK001', 'Fresh Milk 1L', 'Beverages', 3500, 'Dairy Co'),
        ('MILK002', 'UHT Milk 1L', 'Beverages', 3000, 'Dairy Co'),
        ('YOGURT001', 'Plain Yogurt 500ml', 'Beverages', 3000, 'Dairy Co'),
        
        # Vegetables & Fruits (25 items)
        ('TOMATO001', 'Fresh Tomatoes 1kg', 'Vegetables & Fruits', 2500, 'Local Farmers'),
        ('ONION001', 'Red Onions 1kg', 'Vegetables & Fruits', 2000, 'Local Farmers'),
        ('ONION002', 'White Onions 1kg', 'Vegetables & Fruits', 2000, 'Local Farmers'),
        ('POTATO001', 'Potatoes 2kg', 'Vegetables & Fruits', 3000, 'Local Farmers'),
        ('CARROT001', 'Carrots 1kg', 'Vegetables & Fruits', 3500, 'Local Farmers'),
        ('CABBAGE001', 'Green Cabbage 1kg', 'Vegetables & Fruits', 2500, 'Local Farmers'),
        ('CABBAGE002', 'Red Cabbage 1kg', 'Vegetables & Fruits', 3000, 'Local Farmers'),
        ('LETTUCE001', 'Fresh Lettuce 500g', 'Vegetables & Fruits', 2000, 'Local Farmers'),
        ('SPINACH001', 'Fresh Spinach 500g', 'Vegetables & Fruits', 1500, 'Local Farmers'),
        ('PEPPER001', 'Red Pepper 500g', 'Vegetables & Fruits', 3000, 'Local Farmers'),
        ('PEPPER002', 'Green Pepper 500g', 'Vegetables & Fruits', 2500, 'Local Farmers'),
        ('BANANA001', 'Fresh Bananas 1kg', 'Vegetables & Fruits', 2500, 'Local Farmers'),
        ('APPLE001', 'Red Apples 1kg', 'Vegetables & Fruits', 6000, 'Fruit Importers'),
        ('APPLE002', 'Green Apples 1kg', 'Vegetables & Fruits', 6000, 'Fruit Importers'),
        ('ORANGE001', 'Fresh Oranges 1kg', 'Vegetables & Fruits', 4000, 'Fruit Importers'),
        ('MANGO001', 'Fresh Mangoes 1kg', 'Vegetables & Fruits', 5000, 'Fruit Importers'),
        ('AVOCADO001', 'Fresh Avocados 500g', 'Vegetables & Fruits', 4500, 'Fruit Importers'),
        ('PINEAPPLE001', 'Fresh Pineapple 1pc', 'Vegetables & Fruits', 3500, 'Fruit Importers'),
        ('WATERMELON001', 'Fresh Watermelon 1pc', 'Vegetables & Fruits', 5000, 'Fruit Importers'),
        ('PAWPAW001', 'Fresh Pawpaw 1pc', 'Vegetables & Fruits', 2500, 'Local Farmers'),
        ('CUCUMBER001', 'Fresh Cucumbers 1kg', 'Vegetables & Fruits', 2000, 'Local Farmers'),
        ('GARLIC001', 'Fresh Garlic 100g', 'Vegetables & Fruits', 1500, 'Local Farmers'),
        ('GINGER001', 'Fresh Ginger 100g', 'Vegetables & Fruits', 1500, 'Local Farmers'),
        ('LIME001', 'Fresh Limes 1kg', 'Vegetables & Fruits', 3000, 'Fruit Importers'),
        ('LEMON001', 'Fresh Lemons 1kg', 'Vegetables & Fruits', 4000, 'Fruit Importers'),
        
        # Dairy & Cheese (15 items)
        ('CHEESE001', 'Cheddar Cheese 200g', 'Dairy & Cheese', 6500, 'Dairy Co'),
        ('CHEESE002', 'Mozzarella Cheese 250g', 'Dairy & Cheese', 7500, 'Dairy Co'),
        ('CHEESE003', 'Swiss Cheese 200g', 'Dairy & Cheese', 8000, 'Dairy Co'),
        ('EGG001', 'Eggs 12pc', 'Dairy & Cheese', 5000, 'Egg Farmers'),
        ('EGG002', 'Free Range Eggs 12pc', 'Dairy & Cheese', 7000, 'Egg Farmers'),
        ('ICE_CREAM001', 'Vanilla Ice Cream 500ml', 'Dairy & Cheese', 4500, 'Dairy Co'),
        ('ICE_CREAM002', 'Chocolate Ice Cream 500ml', 'Dairy & Cheese', 4500, 'Dairy Co'),
        ('CREAM001', 'Heavy Cream 250ml', 'Dairy & Cheese', 5000, 'Dairy Co'),
        ('SOUR_CREAM001', 'Sour Cream 200ml', 'Dairy & Cheese', 4500, 'Dairy Co'),
        ('COTTAGE_CHEESE001', 'Cottage Cheese 250g', 'Dairy & Cheese', 5500, 'Dairy Co'),
        ('CONDENSED_MILK001', 'Condensed Milk 397g', 'Dairy & Cheese', 4000, 'Dairy Co'),
        ('EVAPORATED_MILK001', 'Evaporated Milk 397g', 'Dairy & Cheese', 3500, 'Dairy Co'),
        ('MILK_POWDER001', 'Milk Powder 500g', 'Dairy & Cheese', 8500, 'Dairy Co'),
        ('BUTTER_MILK001', 'Buttermilk 500ml', 'Dairy & Cheese', 2500, 'Dairy Co'),
        ('LACTOSE_FREE_MILK001', 'Lactose Free Milk 1L', 'Dairy & Cheese', 4500, 'Dairy Co'),
        
        # Meat & Fish (15 items)
        ('CHICKEN001', 'Fresh Chicken 1kg', 'Meat & Fish', 12000, 'Meat Suppliers'),
        ('BEEF001', 'Fresh Beef 1kg', 'Meat & Fish', 18000, 'Meat Suppliers'),
        ('PORK001', 'Fresh Pork 1kg', 'Meat & Fish', 15000, 'Meat Suppliers'),
        ('GOAT001', 'Fresh Goat Meat 1kg', 'Meat & Fish', 16000, 'Meat Suppliers'),
        ('FISH001', 'Fresh Tilapia 1kg', 'Meat & Fish', 10000, 'Fish Market'),
        ('FISH002', 'Smoked Fish 500g', 'Meat & Fish', 6500, 'Fish Market'),
        ('FISH003', 'Dried Fish 500g', 'Meat & Fish', 8000, 'Fish Market'),
        ('SAUSAGE001', 'Pork Sausage 500g', 'Meat & Fish', 7500, 'Meat Suppliers'),
        ('BACON001', 'Bacon Strips 250g', 'Meat & Fish', 8500, 'Meat Suppliers'),
        ('HAM001', 'Canned Ham 400g', 'Meat & Fish', 6500, 'Meat Suppliers'),
        ('CORNED_BEEF001', 'Corned Beef 300g', 'Meat & Fish', 5500, 'Meat Suppliers'),
        ('SARDINE001', 'Canned Sardines 120g', 'Meat & Fish', 3000, 'Fish Market'),
        ('TUNA001', 'Canned Tuna 185g', 'Meat & Fish', 4000, 'Fish Market'),
        ('MACKEREL001', 'Canned Mackerel 150g', 'Meat & Fish', 3500, 'Fish Market'),
        ('SHRIMP001', 'Frozen Shrimp 500g', 'Meat & Fish', 15000, 'Fish Market'),
        
        # Spices & Seasonings (20 items)
        ('SALT001', 'Table Salt 1kg', 'Spices & Seasonings', 1500, 'Salt Traders'),
        ('PEPPER_POWDER001', 'Black Pepper Powder 100g', 'Spices & Seasonings', 3000, 'Spice Co'),
        ('CHILI001', 'Chili Powder 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('CUMIN001', 'Cumin Seeds 100g', 'Spices & Seasonings', 3500, 'Spice Co'),
        ('CORIANDER001', 'Coriander Powder 100g', 'Spices & Seasonings', 3000, 'Spice Co'),
        ('TURMERIC001', 'Turmeric Powder 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('GARLIC_POWDER001', 'Garlic Powder 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('ONION_POWDER001', 'Onion Powder 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('PAPRIKA001', 'Paprika Powder 100g', 'Spices & Seasonings', 3000, 'Spice Co'),
        ('NUTMEG001', 'Nutmeg Powder 100g', 'Spices & Seasonings', 4000, 'Spice Co'),
        ('CINNAMON001', 'Cinnamon Powder 100g', 'Spices & Seasonings', 3500, 'Spice Co'),
        ('GINGER_POWDER001', 'Ginger Powder 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('CLOVES001', 'Cloves 50g', 'Spices & Seasonings', 4500, 'Spice Co'),
        ('CARDAMOM001', 'Cardamom Pods 50g', 'Spices & Seasonings', 5000, 'Spice Co'),
        ('FENUGREEK001', 'Fenugreek Seeds 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('MUSTARD001', 'Mustard Seeds 100g', 'Spices & Seasonings', 2500, 'Spice Co'),
        ('OREGANO001', 'Dried Oregano 50g', 'Spices & Seasonings', 3500, 'Spice Co'),
        ('THYME001', 'Dried Thyme 50g', 'Spices & Seasonings', 3500, 'Spice Co'),
        ('BASIL001', 'Dried Basil 50g', 'Spices & Seasonings', 3500, 'Spice Co'),
        ('ROSEMARY001', 'Dried Rosemary 50g', 'Spices & Seasonings', 3500, 'Spice Co'),
        
        # Condiments & Sauces (15 items)
        ('SAUCE_SOY001', 'Soy Sauce 500ml', 'Condiments & Sauces', 4500, 'Condiment Co'),
        ('SAUCE_TOMATO001', 'Tomato Sauce 500ml', 'Condiments & Sauces', 3500, 'Condiment Co'),
        ('SAUCE_CHILI001', 'Chili Sauce 300ml', 'Condiments & Sauces', 3000, 'Condiment Co'),
        ('SAUCE_WORCESTER001', 'Worcestershire Sauce 150ml', 'Condiments & Sauces', 4000, 'Condiment Co'),
        ('VINEGAR001', 'White Vinegar 500ml', 'Condiments & Sauces', 2000, 'Condiment Co'),
        ('VINEGAR002', 'Apple Cider Vinegar 500ml', 'Condiments & Sauces', 3000, 'Condiment Co'),
        ('MUSTARD_SAUCE001', 'Yellow Mustard 200g', 'Condiments & Sauces', 2500, 'Condiment Co'),
        ('KETCHUP001', 'Tomato Ketchup 300g', 'Condiments & Sauces', 3000, 'Condiment Co'),
        ('BARBECUE_SAUCE001', 'BBQ Sauce 300ml', 'Condiments & Sauces', 4000, 'Condiment Co'),
        ('HOT_SAUCE001', 'Hot Sauce 150ml', 'Condiments & Sauces', 3500, 'Condiment Co'),
        ('CURRY_POWDER001', 'Curry Powder 100g', 'Condiments & Sauces', 3000, 'Condiment Co'),
        ('CURRY_PASTE001', 'Curry Paste 100g', 'Condiments & Sauces', 3500, 'Condiment Co'),
        ('PESTO001', 'Pesto Sauce 100g', 'Condiments & Sauces', 4500, 'Condiment Co'),
        ('SALSA001', 'Salsa Sauce 300ml', 'Condiments & Sauces', 3500, 'Condiment Co'),
        ('SRIRACHA001', 'Sriracha Sauce 200ml', 'Condiments & Sauces', 4000, 'Condiment Co'),
    ]
    
    # create categories first
    category_names = sorted({item[2] for item in products})
    for cname in category_names:
        if not Category.query.filter_by(name=cname).first():
            db.session.add(Category(name=cname))
    db.session.commit()

    for sku, name, category_name, price, supplier in products:
        cat = Category.query.filter_by(name=category_name).first()
        if not Product.query.filter_by(sku=sku).first():
            product = Product(
                sku=sku,
                name=name,
                category_id=cat.id,
                price=price,
                quantity=50,
                min_stock=10,
                supplier=supplier,
                is_active=True
            )
            db.session.add(product)
    db.session.commit()

@app.route('/billing')
def billing():
    return render_template('billing.html')

@app.route('/catalogue')
def catalogue():
    return render_template('catalogue.html')

@app.route('/employees')
def employees():
    return render_template('employees.html')

@app.route('/promotions')
def promotions():
    return render_template('promotions.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Role.query.count() == 0:
            db.session.add_all([
                Role(name='admin', permissions='["admin"]'),
                Role(name='manager', permissions='["manage_employees"]'),
                Role(name='cashier', permissions='["cashier"]'),
                Role(name='attendant', permissions='["attendant"]'),
                Role(name='storemanager', permissions='["storemanager"]'),
            ])
            db.session.commit()
    app.run(debug=True)
