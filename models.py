from flask_login import UserMixin
from datetime import datetime
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    accounts = db.relationship('TradingAccount', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TradingAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shares = db.relationship('Share', backref='account', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('trading_account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def current_price(self):
        # Get the latest price from SharePrice table
        latest_price = SharePrice.query.filter_by(share_name=self.name)\
            .order_by(SharePrice.last_updated.desc())\
            .first()
        return latest_price.current_price if latest_price else self.buying_price

    @property
    def total_investment(self):
        return self.quantity * self.buying_price

    @property
    def current_value(self):
        return self.quantity * self.current_price

    @property
    def profit_loss(self):
        return self.current_value - self.total_investment

    @property
    def profit_loss_percentage(self):
        if self.total_investment == 0:
            return 0
        return (self.profit_loss / self.total_investment) * 100

class SharePrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    share_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class VerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTPToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)
