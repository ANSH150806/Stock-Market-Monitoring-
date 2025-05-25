from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import pymysql

# Use PyMySQL instead of MySQLdb
pymysql.install_as_MySQLdb()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
