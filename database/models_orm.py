from database.orm import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Integer, default=1)
    tagline = db.Column(db.String, default="")
    sort_order = db.Column(db.Integer, default=0)
    parent_id = db.Column(db.Integer, nullable=True)
    is_catalog = db.Column(db.Integer, default=0)
    payment_url = db.Column(db.String, default="")
    promo_price = db.Column(db.String, default="")
    promo_label = db.Column(db.String, default="")
    cost_usd = db.Column(db.Float, default=0.0)
    cost_brl = db.Column(db.Float, default=0.0)
    apply_iof = db.Column(db.Integer, default=1)
    supplier = db.Column(db.String, default="")

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    external_reference = db.Column(db.String, unique=True, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_email = db.Column(db.String, nullable=False)
    amount = db.Column(db.Float)
    status = db.Column(db.String, default='pending')
    key_assigned_id = db.Column(db.Integer, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)
    qr_code_base64 = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Anti-chargeback fields
    customer_name = db.Column(db.String, default="")
    customer_cpf = db.Column(db.String, default="")
    customer_phone = db.Column(db.String, default="")
    ip_purchase = db.Column(db.String, default="")
    ip_delivery = db.Column(db.String, default="")
    terms_accepted_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    user_agent_delivery = db.Column(db.String, default="")
    key_hash = db.Column(db.String, default="")
    recovery_email_sent = db.Column(db.Integer, default=0)

class ManualSale(db.Model):
    __tablename__ = 'manual_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float)
    cost_per_unit_brl = db.Column(db.Float)
    total_price = db.Column(db.Float)
    client_name = db.Column(db.String)
    client_email = db.Column(db.String, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
