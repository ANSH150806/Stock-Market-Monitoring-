from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app import app
from extensions import db, mail
from models import User, TradingAccount, Share, SharePrice, VerificationToken, OTPToken
from share_scraper import get_share_price, get_nifty50_shares, get_sensex_shares, get_top_gainers_losers
import secrets
import random
from datetime import datetime, timedelta

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(user, otp):
    msg = Message('Login Verification Code',
                 sender='noreply@shareportfolio.com',
                 recipients=[user.email])
    msg.html = render_template('emails/otp_email.html',
                             user=user,
                             otp=otp,
                             year=datetime.utcnow().year)
    mail.send(msg)

@app.route('/')
def home():
    nifty_shares = get_nifty50_shares()
    sensex_shares = get_sensex_shares()
    gainers, losers = get_top_gainers_losers()
    return render_template('home.html', 
                         nifty_shares=nifty_shares,
                         sensex_shares=sensex_shares,
                         gainers=gainers,
                         losers=losers)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'error')
            return redirect(url_for('signup'))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        # Generate verification token
        token = secrets.token_urlsafe(32)
        ver_token = VerificationToken(
            user_id=user.id,
            token=token,
            expiry=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(ver_token)
        db.session.commit()

        # Send verification email with HTML template
        msg = Message('Verify your email',
                     sender='noreply@shareportfolio.com',
                     recipients=[email])
        verify_url = url_for('verify_email', token=token, _external=True)
        msg.html = render_template('emails/verification_email.html',
                                 verify_url=verify_url,
                                 year=datetime.utcnow().year)
        mail.send(msg)

        flash('Please check your email to verify your account!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email first!', 'error')
                return redirect(url_for('login'))
            
            # Generate and store OTP
            otp = generate_otp()
            otp_token = OTPToken(
                user_id=user.id,
                otp=otp,
                expiry=datetime.utcnow() + timedelta(minutes=10)
            )
            db.session.add(otp_token)
            db.session.commit()

            # Store user_id in session for OTP verification
            session['temp_user_id'] = user.id
            
            # Send OTP email
            send_otp_email(user, otp)
            
            return redirect(url_for('verify_otp'))
        
        flash('Invalid username or password!', 'error')
    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['temp_user_id']
        otp = request.form.get('otp')
        
        otp_token = OTPToken.query.filter_by(
            user_id=user_id,
            otp=otp,
            is_used=False
        ).order_by(OTPToken.created_at.desc()).first()

        if otp_token and otp_token.expiry > datetime.utcnow():
            user = User.query.get(user_id)
            otp_token.is_used = True
            db.session.commit()
            
            login_user(user)
            session.pop('temp_user_id', None)
            return redirect(url_for('dashboard'))
        
        flash('Invalid or expired OTP!', 'error')
    
    return render_template('verify_otp.html')

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'temp_user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['temp_user_id'])
    if user:
        # Generate and store new OTP
        otp = generate_otp()
        otp_token = OTPToken(
            user_id=user.id,
            otp=otp,
            expiry=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(otp_token)
        db.session.commit()

        # Send new OTP email
        send_otp_email(user, otp)
        flash('New OTP has been sent to your email!', 'success')
    
    return redirect(url_for('verify_otp'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            ver_token = VerificationToken(
                user_id=user.id,
                token=token,
                expiry=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(ver_token)
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset Your Password',
                         sender='noreply@shareportfolio.com',
                         recipients=[email])
            msg.html = render_template('emails/reset_password.html',
                                     reset_url=reset_url,
                                     year=datetime.utcnow().year)
            mail.send(msg)
            
            flash('Password reset instructions sent to your email!', 'success')
            return redirect(url_for('login'))
        
        flash('Email not found!', 'error')
    return render_template('forgot_password.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    ver_token = VerificationToken.query.filter_by(token=token).first()
    if ver_token and ver_token.expiry > datetime.utcnow():
        user = User.query.get(ver_token.user_id)
        user.is_verified = True
        db.session.delete(ver_token)
        db.session.commit()
        flash('Email verified successfully!', 'success')
        return redirect(url_for('login'))
    flash('Invalid or expired verification link!', 'error')
    return redirect(url_for('login'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    ver_token = VerificationToken.query.filter_by(token=token).first()
    if not ver_token or ver_token.expiry < datetime.utcnow():
        flash('Invalid or expired reset link!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('reset_password', token=token))

        user = User.query.get(ver_token.user_id)
        user.password = generate_password_hash(password)
        db.session.delete(ver_token)
        db.session.commit()

        flash('Password reset successful!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    accounts = TradingAccount.query.filter_by(user_id=current_user.id).all()
    portfolio_summary = {}
    total_portfolio = {
        'total_investment': 0,
        'current_value': 0,
        'profit_loss': 0,
        'profit_loss_percentage': 0
    }

    for account in accounts:
        summary = {
            'total_investment': 0,
            'current_value': 0,
            'profit_loss': 0,
            'profit_loss_percentage': 0
        }
        
        for share in account.shares:
            # Update share price in database
            current_price = get_share_price(share.name)
            if current_price:
                share_price = SharePrice(
                    share_name=share.name,
                    current_price=current_price
                )
                db.session.add(share_price)
                db.session.commit()

            summary['total_investment'] += share.total_investment
            summary['current_value'] += share.current_value
            summary['profit_loss'] += share.profit_loss
        
        if summary['total_investment'] > 0:
            summary['profit_loss_percentage'] = (summary['profit_loss'] / summary['total_investment']) * 100
        
        portfolio_summary[account.id] = summary
        
        total_portfolio['total_investment'] += summary['total_investment']
        total_portfolio['current_value'] += summary['current_value']
        total_portfolio['profit_loss'] += summary['profit_loss']
    
    if total_portfolio['total_investment'] > 0:
        total_portfolio['profit_loss_percentage'] = (total_portfolio['profit_loss'] / total_portfolio['total_investment']) * 100

    return render_template('dashboard.html',
                         accounts=accounts,
                         portfolio_summary=portfolio_summary,
                         total_portfolio=total_portfolio)

@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    name = request.form.get('name')
    if name:
        account = TradingAccount(name=name, user_id=current_user.id)
        db.session.add(account)
        db.session.commit()
        flash('Account added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_share', methods=['POST'])
@login_required
def add_share():
    account_id = request.form.get('account_id')
    share_name = request.form.get('share_name')
    quantity = request.form.get('quantity')
    buying_price = request.form.get('buying_price')

    if all([account_id, share_name, quantity, buying_price]):
        share = Share(
            name=share_name,
            quantity=int(quantity),
            buying_price=float(buying_price),
            account_id=int(account_id)
        )
        db.session.add(share)
        db.session.commit()
        flash('Share added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/remove_share/<int:share_id>', methods=['POST'])
@login_required
def remove_share(share_id):
    share = Share.query.get_or_404(share_id)
    if share.account.user_id == current_user.id:
        db.session.delete(share)
        db.session.commit()
        flash('Share removed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
