# Share Market Portfolio Management System

A web application for managing multiple share market trading accounts in one place.

## Features
- Multi-account portfolio management
- Real-time share price tracking
- Portfolio performance analysis
- Email verification system
- Secure authentication
- Automated share price updates

## Prerequisites
- Python 3.8
- MySQL (XAMPP or standalone MySQL server)
- SMTP server for email functionality
- Git (for cloning the repository)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd share-market-portfolio
```

2. Create and activate a virtual environment:
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On Linux/Mac:
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure MySQL Database:
- Start MySQL server (via XAMPP or standalone)
- The application will automatically create the database on first run
- Default database name: 'share_portfolio'

5. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
# Database Configuration
DATABASE_URL=mysql://username:password@localhost/share_portfolio

# Email Configuration
MAIL_SERVER=your_smtp_server
MAIL_PORT=587
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=True

# Security
SECRET_KEY=your_secret_key_here

# Optional: Debug mode
FLASK_DEBUG=True
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure
```
share_portfolio/
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
├── app.py              # Main application file
├── routes.py           # Route definitions
├── models.py           # Database models
├── extensions.py       # Flask extensions
├── share_scraper.py    # Share price scraping functionality
├── requirements.txt    # Project dependencies
└── .env               # Environment variables (create this)
```

## Troubleshooting

1. Database Connection Issues:
- Verify MySQL is running
- Check database credentials in .env file
- Ensure MySQL user has proper permissions

2. Email Verification Issues:
- Check SMTP settings in .env file
- For Gmail, use App Password instead of account password
- Verify port 587 is not blocked by firewall

3. Dependencies Issues:
- Make sure virtual environment is activated
- Try removing venv folder and recreating it
- Update pip: `python -m pip install --upgrade pip`

## Security Notes
- Never commit .env file to version control
- Regularly update dependencies for security patches
- Use strong, unique passwords for database and email

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
