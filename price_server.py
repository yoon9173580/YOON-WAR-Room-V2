from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

class GMEPriceService:
    def __init__(self):
        self.price_cache = {}
        self.cache_timeout = 30  # 30 seconds cache
        self.last_update = None
        self.base_price = 25.00
        
    def get_gme_price(self):
        """Get current GME price from Yahoo Finance API"""
        try:
            # Check cache first
            if 'gme_price' in self.price_cache:
                cached_time, cached_price = self.price_cache['gme_price']
                if time.time() - cached_time < self.cache_timeout:
                    return cached_price
            
            # Fetch from Yahoo Finance
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GME"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
                self.price_cache['gme_price'] = (time.time(), current_price)
                self.last_update = datetime.now()
                return current_price
            else:
                return self.base_price
                
        except Exception as e:
            print(f"Error fetching GME price: {e}")
            return self.base_price
    
    def get_market_status(self):
        """Check if market is open"""
        now = datetime.now()
        # Simple market hours check (9:30 AM - 4:00 PM ET, Mon-Fri)
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close

price_service = GMEPriceService()

@app.route('/api/gme-price')
def get_gme_price():
    """API endpoint to get current GME price"""
    current_price = price_service.get_gme_price()
    price_ratio = current_price / price_service.base_price
    
    return jsonify({
        'price': current_price,
        'price_ratio': price_ratio,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_open': price_service.get_market_status(),
        'last_update': price_service.last_update.strftime('%Y-%m-%d %H:%M:%S') if price_service.last_update else None
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_open': price_service.get_market_status()
    })

def background_price_updater():
    """Background thread to update prices periodically"""
    while True:
        try:
            price_service.get_gme_price()
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            print(f"Background updater error: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == '__main__':
    # Start background price updater
    updater_thread = threading.Thread(target=background_price_updater, daemon=True)
    updater_thread.start()
    
    print("Starting GME Price Server...")
    print("Available endpoints:")
    print("  - GET /api/gme-price - Get current GME price")
    print("  - GET /api/health - Health check")
    print("\nServer running on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
