import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json
from models import SharePrice, db
from time import sleep
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_number(text):
    """Clean number string by removing commas, spaces, and converting percentage"""
    if not text:
        return 0
    try:
        # Remove currency symbols, commas, spaces, and % symbol
        cleaned = text.replace('₹', '').replace(',', '').replace(' ', '').replace('%', '').strip()
        if cleaned:
            return float(cleaned)
        return 0
    except ValueError:
        return 0

def get_share_price(share_name):
    """Get current share price from Google Finance"""
    try:
        # First check if we have a recent price in our database
        share_price = SharePrice.query.filter_by(share_name=share_name).first()
        if share_price and (datetime.utcnow() - share_price.last_updated).seconds < 300:  # 5 minutes cache
            return share_price.current_price

        # If no recent price, scrape from Google Finance
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        # Search for the stock on Google Finance
        search_url = f"https://www.google.com/finance/quote/{share_name}:NSE"
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the price div
            price_div = soup.find('div', {'class': 'YMlKec fxKbKc'})
            if price_div:
                try:
                    price = clean_number(price_div.text)
                    if price > 0:
                        # Update or create price in database
                        if share_price:
                            share_price.current_price = price
                            share_price.last_updated = datetime.utcnow()
                        else:
                            share_price = SharePrice(
                                share_name=share_name,
                                current_price=price
                            )
                            db.session.add(share_price)
                        
                        db.session.commit()
                        logger.info(f"Successfully updated price for {share_name}: {price}")
                        return price
                    
                except ValueError as e:
                    logger.error(f"Error converting price for {share_name}: {e}")
            else:
                # Try BSE if NSE fails
                bse_url = f"https://www.google.com/finance/quote/{share_name}:BSE"
                bse_response = requests.get(bse_url, headers=headers)
                if bse_response.status_code == 200:
                    bse_soup = BeautifulSoup(bse_response.text, 'html.parser')
                    price_div = bse_soup.find('div', {'class': 'YMlKec fxKbKc'})
                    if price_div:
                        try:
                            price = clean_number(price_div.text)
                            if price > 0:
                                if share_price:
                                    share_price.current_price = price
                                    share_price.last_updated = datetime.utcnow()
                                else:
                                    share_price = SharePrice(
                                        share_name=share_name,
                                        current_price=price
                                    )
                                    db.session.add(share_price)
                                
                                db.session.commit()
                                logger.info(f"Successfully updated price for {share_name} from BSE: {price}")
                                return price
                        except ValueError as e:
                            logger.error(f"Error converting BSE price for {share_name}: {e}")
    
        logger.error(f"Could not find price for {share_name} on Google Finance")
        return None
            
    except Exception as e:
        logger.error(f"Error fetching price for {share_name}: {e}")
        return None

def get_nifty50_shares():
    """Get Nifty 50 shares data"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        url = "https://www.google.com/finance/quote/.NSEI:INDEXNSE"
        response = requests.get(url, headers=headers)
        
        shares = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            constituents = soup.find_all('div', {'class': 'SxcTic'})
            
            for constituent in constituents[:50]:  # Get top 50 shares
                try:
                    symbol = constituent.find('div', {'class': 'ZvmM7'}).text.strip()
                    price_div = constituent.find('div', {'class': 'YMlKec'})
                    change_div = constituent.find('div', {'class': 'JwB6zf'})
                    
                    price = clean_number(price_div.text) if price_div else 0
                    change = clean_number(change_div.text.split('(')[0]) if change_div else 0
                    change_percent = clean_number(change_div.text.split('(')[1].split(')')[0]) if change_div and '(' in change_div.text else 0
                    
                    share_data = {
                        'symbol': symbol,
                        'ltp': price,
                        'change': change,
                        'percentageChange': change_percent
                    }
                    shares.append(share_data)
                except Exception as e:
                    logger.error(f"Error parsing Nifty50 constituent data: {e}")
                    continue
        
        return shares
    except Exception as e:
        logger.error(f"Error getting Nifty 50 shares: {e}")
        return []

def get_sensex_shares():
    """Get Sensex shares data"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        url = "https://www.google.com/finance/quote/.BSESN:INDEXBOM"
        response = requests.get(url, headers=headers)
        
        shares = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            constituents = soup.find_all('div', {'class': 'SxcTic'})
            
            for constituent in constituents[:30]:  # Get top 30 shares
                try:
                    symbol = constituent.find('div', {'class': 'ZvmM7'}).text.strip()
                    price_div = constituent.find('div', {'class': 'YMlKec'})
                    change_div = constituent.find('div', {'class': 'JwB6zf'})
                    
                    price = clean_number(price_div.text) if price_div else 0
                    change = clean_number(change_div.text.split('(')[0]) if change_div else 0
                    change_percent = clean_number(change_div.text.split('(')[1].split(')')[0]) if change_div and '(' in change_div.text else 0
                    
                    share_data = {
                        'symbol': symbol,
                        'ltp': price,
                        'change': change,
                        'percentageChange': change_percent
                    }
                    shares.append(share_data)
                except Exception as e:
                    logger.error(f"Error parsing Sensex constituent data: {e}")
                    continue
        
        return shares
    except Exception as e:
        logger.error(f"Error getting Sensex shares: {e}")
        return []

def get_top_gainers_losers():
    """Get top gainers and losers from Google Finance"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        def scrape_stocks(url):
            response = requests.get(url, headers=headers)
            stocks = []
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                constituents = soup.find_all('div', {'class': 'SxcTic'})
                
                for constituent in constituents[:5]:  # Get top 5
                    try:
                        symbol = constituent.find('div', {'class': 'ZvmM7'}).text.strip()
                        price_div = constituent.find('div', {'class': 'YMlKec'})
                        change_div = constituent.find('div', {'class': 'JwB6zf'})
                        
                        price = clean_number(price_div.text) if price_div else 0
                        change = clean_number(change_div.text.split('(')[0]) if change_div else 0
                        change_percent = clean_number(change_div.text.split('(')[1].split(')')[0]) if change_div and '(' in change_div.text else 0
                        
                        stock_data = {
                            'symbol': symbol,
                            'ltp': price,
                            'change': change,
                            'percentageChange': change_percent
                        }
                        stocks.append(stock_data)
                    except Exception as e:
                        logger.error(f"Error parsing stock data: {e}")
                        continue
            
            return stocks
        
        # Get top gainers from NSE
        gainers = scrape_stocks("https://www.google.com/finance/markets/gainers?hl=en")
        
        # Get top losers from NSE
        losers = scrape_stocks("https://www.google.com/finance/markets/losers?hl=en")
        
        return gainers, losers
    except Exception as e:
        logger.error(f"Error getting top gainers/losers: {e}")
        return [], []

def format_share_data(share_data):
    """Format share data for display"""
    try:
        return {
            'name': share_data.get('symbol', ''),
            'price': clean_number(share_data.get('ltp', 0)),
            'change': clean_number(share_data.get('change', 0)),
            'change_percent': clean_number(share_data.get('percentageChange', 0)),
            'volume': int(clean_number(share_data.get('volume', 0))),
            'high': clean_number(share_data.get('high', 0)),
            'low': clean_number(share_data.get('low', 0)),
            'open': clean_number(share_data.get('open', 0)),
            'close': clean_number(share_data.get('close', 0))
        }
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting share data: {e}")
        return None
