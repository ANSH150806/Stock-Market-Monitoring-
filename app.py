from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
import os
from dotenv import load_dotenv
import pymysql
from extensions import db, mail, login_manager

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# First create database if it doesn't exist
def create_database():
    try:
        # Parse the DATABASE_URL
        db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/share_portfolio')
        parts = db_url.split('/')
        db_name = parts[-1]
        base_url = '/'.join(parts[:-1])
        
        # Create connection without database name
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # Create database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                print(f"Database {db_name} created successfully!")
        finally:
            connection.close()
    except Exception as e:
        print(f"Error creating database: {e}")

# Create database before setting up SQLAlchemy
create_database()

# Now set up SQLAlchemy with the full database URL using PyMySQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/share_portfolio')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Initialize extensions with app
db.init_app(app)
mail.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models
from models import User, TradingAccount, Share, SharePrice, VerificationToken

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/remove_account/<int:account_id>', methods=['POST'])
@login_required
def remove_account(account_id):
    account = TradingAccount.query.filter_by(id=account_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete associated shares first (due to foreign key constraints)
        Share.query.filter_by(account_id=account_id).delete()
        
        # Delete the account
        db.session.delete(account)
        db.session.commit()
        
        flash('Trading account removed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error removing trading account. Please try again.', 'danger')
        app.logger.error(f"Error removing account {account_id}: {str(e)}")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Import routes after all models and extensions are initialized
    from routes import *
    
    with app.app_context():
        db.create_all()
    app.run(debug=True)
