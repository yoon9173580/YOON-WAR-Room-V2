import json
import requests
from datetime import datetime
import time

class GMEPriceTracker:
    def __init__(self):
        self.price_cache = {}
        self.cache_timeout = 300  # 5 minutes cache
        
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
            
            current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
            
            # Cache the price
            self.price_cache['gme_price'] = (time.time(), current_price)
            
            return current_price
            
        except Exception as e:
            print(f"Error fetching GME price: {e}")
            return 25.00  # Default fallback price

class DynamicPipeline:
    def __init__(self):
        self.price_tracker = GMEPriceTracker()
        self.base_gme_price = 25.00  # Reference price for calculations
        
        # Base allocation values (at $25/share)
        self.base_allocations = {
            'cs_shares': 100000,
            'fid_balance': 904560,
            'moo_balance': 1500870,
            'st2_total': 578788
        }
        
    def calculate_dynamic_allocations(self):
        """Calculate allocations based on current GME price"""
        current_price = self.price_tracker.get_gme_price()
        price_ratio = current_price / self.base_gme_price
        
        # Adjust share counts based on price
        cs_cost = self.base_allocations['cs_shares'] * current_price
        
        # Option allocations remain as percentage of balance
        fid_options = self.base_allocations['fid_balance']
        moo_options = self.base_allocations['moo_balance']
        
        return {
            'gme_price': current_price,
            'cs_shares': self.base_allocations['cs_shares'],
            'cs_cost': cs_cost,
            'fid_options': fid_options,
            'moo_options': moo_options,
            'st2_total': self.base_allocations['st2_total'],
            'price_ratio': price_ratio
        }
    
    def generate_html_snippet(self):
        """Generate HTML snippet with dynamic pricing"""
        allocations = self.calculate_dynamic_allocations()
        
        html = f"""
        <!-- DYNAMIC GME PRICING SNIPPET -->
        <div class="price-header">
            <div class="current-price">
                <span class="price-label">GME Current Price:</span>
                <span class="price-value">${allocations['gme_price']:.2f}</span>
                <span class="price-ratio">{allocations['price_ratio']:.2f}x base</span>
            </div>
            <div class="last-updated">
                Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <script>
        function updateGMEPrice() {{
            fetch('/api/gme-price')
                .then(response => response.json())
                .then(data => {{
                    document.querySelector('.price-value').textContent = '$' + data.price.toFixed(2);
                    document.querySelector('.price-ratio').textContent = data.price_ratio.toFixed(2) + 'x base';
                    document.querySelector('.last-updated').textContent = 'Last Updated: ' + data.timestamp;
                    
                    // Update all GME-related values
                    updatePipelineValues(data);
                }})
                .catch(error => console.error('Error updating price:', error));
        }}
        
        function updatePipelineValues(priceData) {{
            // Update CS shares cost
            const csElements = document.querySelectorAll('[data-cs-cost]');
            csElements.forEach(el => {{
                const baseCost = parseFloat(el.dataset.baseCost);
                const newCost = baseCost * priceData.price_ratio;
                el.textContent = '-' + formatCurrency(newCost);
            }});
            
            // Update share counts if needed
            const shareElements = document.querySelectorAll('[data-share-count]');
            shareElements.forEach(el => {{
                const baseShares = parseInt(el.dataset.baseShares);
                const newShares = Math.floor(baseShares / priceData.price_ratio);
                el.textContent = formatNumber(newShares) + '주';
            }});
        }}
        
        function formatCurrency(amount) {{
            return '$' + amount.toLocaleString('en-US', {{minimumFractionDigits: 0, maximumFractionDigits: 0}});
        }}
        
        function formatNumber(num) {{
            return num.toLocaleString('en-US');
        }}
        
        // Update price every 30 seconds during market hours
        setInterval(updateGMEPrice, 30000);
        </script>
        """
        
        return html

    def generate_enhanced_pipeline(self):
        """Generate enhanced pipeline with better visibility and dynamic pricing"""
        allocations = self.calculate_dynamic_allocations()
        
        pipeline_html = f"""
        <!-- ENHANCED PIPELINE WITH DYNAMIC PRICING -->
        <div class="pipeline-container">
            <div class="pipeline-header">
                <h2>YOON MASTER COMMAND — Dynamic GME Pipeline</h2>
                <div class="market-status">
                    <span class="status-indicator active"></span>
                    <span class="status-text">Market Hours: Active</span>
                </div>
            </div>
            
            {self.generate_html_snippet()}
            
            <div class="stages-overview">
                <div class="stage-card st2">
                    <div class="stage-header">
                        <h3>ST 2</h3>
                        <span class="stage-title">즉시 집행금</span>
                    </div>
                    <div class="stage-total">
                        <span class="amount">-{format_currency(allocations['st2_total'])}</span>
                        <span class="description">Immediate Rewards</span>
                    </div>
                </div>
                
                <div class="stage-card st3">
                    <div class="stage-header">
                        <h3>ST 3</h3>
                        <span class="stage-title">브로커 전액 GME 투입</span>
                    </div>
                    <div class="stage-total">
                        <span class="amount">-{format_currency(allocations['cs_cost'] + allocations['fid_options'] + allocations['moo_options'])}</span>
                        <span class="description">Broker-Isolated Pipeline</span>
                    </div>
                    <div class="stage-breakdown">
                        <div class="breakdown-item">
                            <span class="label">CS 현물:</span>
                            <span class="value" data-cs-cost="{3500000}">-{format_currency(allocations['cs_cost'])}</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="label">Fid 옵션:</span>
                            <span class="value">-{format_currency(allocations['fid_options'])}</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="label">Moo 옵션:</span>
                            <span class="value">-{format_currency(allocations['moo_options'])}</span>
                        </div>
                    </div>
                </div>
                
                <div class="stage-card st4">
                    <div class="stage-header">
                        <h3>ST 4</h3>
                        <span class="stage-title">절세 제국 스케일업</span>
                    </div>
                    <div class="stage-total">
                        <span class="amount">-${format_currency(int(13058145 * allocations['price_ratio']))}</span>
                        <span class="description">BBBY + GME STCG Offset</span>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
        .pipeline-container {{
            background: var(--bg2);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
        }}
        
        .pipeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}
        
        .pipeline-header h2 {{
            font-family: var(--disp);
            font-size: 24px;
            font-weight: 700;
            color: var(--text);
        }}
        
        .market-status {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .status-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--bull);
            animation: pulse 2s infinite;
        }}
        
        .status-indicator.inactive {{
            background: var(--textD);
            animation: none;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .price-header {{
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .current-price {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .price-label {{
            color: var(--textM);
            font-size: 12px;
        }}
        
        .price-value {{
            font-family: var(--mono);
            font-size: 18px;
            font-weight: 600;
            color: var(--accent);
        }}
        
        .price-ratio {{
            font-size: 12px;
            color: var(--textM);
            background: var(--bg4);
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .last-updated {{
            font-size: 11px;
            color: var(--textD);
        }}
        
        .stages-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .stage-card {{
            background: var(--bg3);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        
        .stage-card:hover {{
            transform: translateY(-2px);
            border-color: var(--borderB);
        }}
        
        .stage-card.st2 {{ border-left: 4px solid var(--amber); }}
        .stage-card.st3 {{ border-left: 4px solid var(--purple); }}
        .stage-card.st4 {{ border-left: 4px solid var(--bull); }}
        
        .stage-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        
        .stage-header h3 {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text);
        }}
        
        .stage-title {{
            font-size: 12px;
            color: var(--textM);
        }}
        
        .stage-total {{
            margin-bottom: 16px;
        }}
        
        .stage-total .amount {{
            display: block;
            font-size: 24px;
            font-weight: 700;
            color: var(--bear);
            margin-bottom: 4px;
        }}
        
        .stage-total .description {{
            font-size: 11px;
            color: var(--textD);
        }}
        
        .stage-breakdown {{
            border-top: 1px solid var(--border);
            padding-top: 12px;
        }}
        
        .breakdown-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 0;
            font-size: 12px;
        }}
        
        .breakdown-item .label {{
            color: var(--textM);
        }}
        
        .breakdown-item .value {{
            font-family: var(--mono);
            font-weight: 500;
            color: var(--text);
        }}
        
        @media (max-width: 768px) {{
            .stages-overview {{
                grid-template-columns: 1fr;
            }}
            
            .pipeline-header {{
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }}
            
            .price-header {{
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }}
        }}
        </style>
        """
        
        return pipeline_html

def format_currency(amount):
    """Format currency with commas"""
    return f"{int(amount):,}"

if __name__ == "__main__":
    pipeline = DynamicPipeline()
    html_content = pipeline.generate_enhanced_pipeline()
    
    with open('enhanced_pipeline.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Enhanced pipeline with dynamic pricing generated!")
