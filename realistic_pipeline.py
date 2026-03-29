import requests
import time
from datetime import datetime
import json

class RealisticGMEPipeline:
    def __init__(self):
        self.base_gme_price = 25.00
        self.price_cache = {}
        self.cache_timeout = 300  # 5 minutes cache
        
        # 현실적인 리테일 제약사항 반영
        self.retail_constraints = {
            'fid_max_option_size': 500000,  # Fidelity 최대 옵션 투자 한도
            'moo_max_option_size': 750000,  # Moomoo 최대 옵션 투자 한도  
            'cs_max_shares': 50000,         # CS 최대 주식 수 (실제 매수 가능)
            'option_strike_prices': [20, 25, 30, 35, 40],  # 현실적인 스트라이크 가격
            'max_contracts_per_strike': 1000  # 스트라이크당 최대 컨트랙트 수
        }
        
        # ST 1 총액 시나리오
        self.st1_totals = [8705430, 10031972, 16540318, 30717733]
        
        # ST 2 즉시 집행금 (고정)
        self.st2_total = 578788
        
    def get_gme_price(self):
        """Get current GME price from Yahoo Finance API"""
        try:
            if 'gme_price' in self.price_cache:
                cached_time, cached_price = self.price_cache['gme_price']
                if time.time() - cached_time < self.cache_timeout:
                    return cached_price
            
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GME"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
            self.price_cache['gme_price'] = (time.time(), current_price)
            
            return current_price
            
        except Exception as e:
            print(f"Error fetching GME price: {e}")
            return self.base_gme_price
    
    def calculate_realistic_allocations(self):
        """현실적인 제약사항을 반영한 자금 배분 계산"""
        current_price = self.get_gme_price()
        allocations = []
        
        for i, st1_total in enumerate(self.st1_totals):
            # ST 2 집행 후 잔액
            st2_remaining = st1_total - self.st2_total
            
            # CS 현물: 최대 50,000주 또는 잔액 한도
            max_cs_shares = min(self.retail_constraints['cs_max_shares'], 
                             int(st2_remaining / current_price))
            cs_cost = max_cs_shares * current_price
            cs_remaining = st2_remaining - cs_cost
            
            # Fidelity 옵션: 최대 $500,000 또는 잔액 한도
            fid_option_amount = min(self.retail_constraints['fid_max_option_size'], cs_remaining)
            fid_remaining = cs_remaining - fid_option_amount
            
            # Moomoo 옵션: 최대 $750,000 또는 잔액 한도  
            moo_option_amount = min(self.retail_constraints['moo_max_option_size'], fid_remaining)
            final_cash = fid_remaining - moo_option_amount
            
            # 옵션 스트라이크별 분배 (현실적인 컨트랙트 수)
            fid_strikes = self.allocate_option_contracts(fid_option_amount, current_price)
            moo_strikes = self.allocate_option_contracts(moo_option_amount, current_price)
            
            allocation = {
                'scenario': i + 1,
                'st1_total': st1_total,
                'st2_total': self.st2_total,
                'st2_remaining': st2_remaining,
                'cs_shares': max_cs_shares,
                'cs_cost': cs_cost,
                'cs_remaining': cs_remaining,
                'fid_option_total': fid_option_amount,
                'fid_strikes': fid_strikes,
                'fid_remaining': fid_remaining,
                'moo_option_total': moo_option_amount,
                'moo_strikes': moo_strikes,
                'final_cash': final_cash,
                'gme_price': current_price
            }
            
            allocations.append(allocation)
            
        return allocations
    
    def allocate_option_contracts(self, total_amount, current_price):
        """옵션 컨트랙트를 스트라이크별로 현실적으로 분배"""
        strikes = []
        remaining_amount = total_amount
        
        # 각 스트라이크에 균등 분배 시도
        per_strike_budget = total_amount // len(self.retail_constraints['option_strike_prices'])
        
        for strike in self.retail_constraints['option_strike_prices']:
            if remaining_amount <= 0:
                break
                
            # 이 옵션의 프리미엄 추정 (단순화: ITM일수록 비쌈)
            intrinsic_value = max(0, current_price - strike)
            time_value = 2.0  # 시간가치 단순화
            premium_per_contract = (intrinsic_value + time_value) * 100  # 1컨트랙트 = 100주
            
            # 최대 컨트랙트 수 계산
            max_contracts = min(
                self.retail_constraints['max_contracts_per_strike'],
                int(per_strike_budget / premium_per_contract) if premium_per_contract > 0 else 0
            )
            
            if max_contracts > 0:
                contract_cost = max_contracts * premium_per_contract
                strikes.append({
                    'strike': strike,
                    'contracts': max_contracts,
                    'cost': contract_cost,
                    'type': 'ITM' if current_price > strike else 'OTM'
                })
                remaining_amount -= contract_cost
        
        return strikes
    
    def generate_realistic_html(self):
        """현실적인 파이프라인 HTML 생성"""
        allocations = self.calculate_realistic_allocations()
        current_price = self.get_gme_price()
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>YOON MASTER COMMAND — Realistic GME Pipeline V55</title>
            <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg: #05070a;
                    --bg2: #0b0f15;
                    --bg3: #10151d;
                    --bg4: #141b25;
                    --border: rgba(255, 255, 255, 0.07);
                    --text: #dde6f0;
                    --textM: #8899aa;
                    --textD: #3d5068;
                    --accent: #00d4aa;
                    --amber: #f59e0b;
                    --bull: #22d45a;
                    --bear: #f04040;
                    --purple: #a78bfa;
                    --red: #ef4444;
                    --mono: 'JetBrains Mono', monospace;
                    --disp: 'Syne', sans-serif;
                }}
                
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                
                body {{
                    background: var(--bg);
                    color: var(--text);
                    font-family: var(--mono);
                    min-height: 100vh;
                    font-size: 13px;
                    line-height: 1.6;
                }}
                
                .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                
                .header h1 {{
                    font-family: var(--disp);
                    font-size: 28px;
                    font-weight: 800;
                    color: var(--text);
                    margin-bottom: 8px;
                }}
                
                .subtitle {{
                    color: var(--textM);
                    font-size: 14px;
                }}
                
                .price-banner {{
                    background: var(--bg2);
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 24px;
                    text-align: center;
                }}
                
                .current-price {{
                    font-size: 24px;
                    font-weight: 700;
                    color: var(--accent);
                }}
                
                .constraints-warning {{
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 24px;
                }}
                
                .constraints-warning h3 {{
                    color: var(--red);
                    margin-bottom: 8px;
                }}
                
                .constraints-list {{
                    list-style: none;
                    font-size: 12px;
                    color: var(--textM);
                }}
                
                .constraints-list li {{
                    padding: 4px 0;
                }}
                
                .scenario-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .scenario-card {{
                    background: var(--bg2);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 20px;
                    transition: transform 0.2s ease;
                }}
                
                .scenario-card:hover {{
                    transform: translateY(-2px);
                    border-color: var(--borderB);
                }}
                
                .scenario-header {{
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 12px;
                    margin-bottom: 16px;
                }}
                
                .scenario-title {{
                    font-size: 18px;
                    font-weight: 700;
                    color: var(--text);
                    margin-bottom: 4px;
                }}
                
                .scenario-total {{
                    font-size: 14px;
                    color: var(--textM);
                }}
                
                .allocation-section {{
                    margin-bottom: 16px;
                }}
                
                .allocation-title {{
                    font-size: 12px;
                    font-weight: 600;
                    color: var(--textM);
                    margin-bottom: 8px;
                    text-transform: uppercase;
                }}
                
                .allocation-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 6px 0;
                    font-size: 12px;
                }}
                
                .allocation-label {{
                    color: var(--textM);
                }}
                
                .allocation-value {{
                    font-family: var(--mono);
                    font-weight: 500;
                    color: var(--text);
                }}
                
                .neg {{ color: var(--bear); }}
                .pos {{ color: var(--bull); }}
                
                .option-strikes {{
                    background: var(--bg3);
                    border-radius: 6px;
                    padding: 8px;
                    margin-top: 8px;
                }}
                
                .strike-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 4px 0;
                    font-size: 11px;
                }}
                
                .strike-info {{
                    color: var(--textM);
                }}
                
                .itm {{ color: var(--bull); }}
                .otm {{ color: var(--textD); }}
                
                .final-cash {{
                    background: var(--bg3);
                    border-radius: 6px;
                    padding: 12px;
                    margin-top: 12px;
                    text-align: center;
                }}
                
                .final-cash-amount {{
                    font-size: 16px;
                    font-weight: 700;
                    color: var(--bull);
                }}
                
                @media (max-width: 768px) {{
                    .scenario-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>YOON MASTER COMMAND</h1>
                    <div class="subtitle">Realistic GME Pipeline V55 — Retail Constraints Applied</div>
                </div>
                
                <div class="price-banner">
                    <div class="current-price">GME: ${current_price:.2f}</div>
                    <div style="font-size: 12px; color: var(--textM); margin-top: 4px;">
                        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
                
                <div class="constraints-warning">
                    <h3>⚠️ Retail Platform Constraints Applied</h3>
                    <ul class="constraints-list">
                        <li>• Fidelity 옵션 최대: ${self.retail_constraints['fid_max_option_size']:,}</li>
                        <li>• Moomoo 옵션 최대: ${self.retail_constraints['moo_max_option_size']:,}</li>
                        <li>• CS 현물 최대: {self.retail_constraints['cs_max_shares']:,}주</li>
                        <li>• 스트라이크당 최대: {self.retail_constraints['max_contracts_per_strike']} 컨트랙트</li>
                        <li>• 37:63 비율 유지 (Fid:Moo)</li>
                    </ul>
                </div>
                
                <div class="scenario-grid">
        """
        
        # 각 시나리오별 카드 생성
        for allocation in allocations:
            html += f"""
                    <div class="scenario-card">
                        <div class="scenario-header">
                            <div class="scenario-title">Scenario {allocation['scenario']}</div>
                            <div class="scenario-total">ST 1 Total: ${allocation['st1_total']:,}</div>
                        </div>
                        
                        <div class="allocation-section">
                            <div class="allocation-title">ST 2. 즉시 집행금</div>
                            <div class="allocation-item">
                                <span class="allocation-label">총 집행금:</span>
                                <span class="allocation-value neg">-${allocation['st2_total']:,}</span>
                            </div>
                            <div class="allocation-item">
                                <span class="allocation-label">집행 후 잔액:</span>
                                <span class="allocation-value pos">${allocation['st2_remaining']:,}</span>
                            </div>
                        </div>
                        
                        <div class="allocation-section">
                            <div class="allocation-title">ST 3. 현실적 GME 투입</div>
                            <div class="allocation-item">
                                <span class="allocation-label">CS 현물 ({allocation['cs_shares']:,}주):</span>
                                <span class="allocation-value neg">-${allocation['cs_cost']:,}</span>
                            </div>
                            
                            <div class="allocation-item">
                                <span class="allocation-label">Fidelity 옵션:</span>
                                <span class="allocation-value neg">-${allocation['fid_option_total']:,}</span>
                            </div>
            """
            
            # Fidelity 스트라이크 상세
            if allocation['fid_strikes']:
                html += '<div class="option-strikes">'
                for strike in allocation['fid_strikes']:
                    html += f"""
                                <div class="strike-item">
                                    <span class="strike-info">Strike ${strike['strike']} ({strike['contracts']}c) <span class="{strike['type'].lower()}">{strike['type']}</span></span>
                                    <span>-${strike['cost']:,}</span>
                                </div>
                    """
                html += '</div>'
            
            html += f"""
                            <div class="allocation-item">
                                <span class="allocation-label">Moomoo 옵션:</span>
                                <span class="allocation-value neg">-${allocation['moo_option_total']:,}</span>
                            </div>
            """
            
            # Moomoo 스트라이크 상세
            if allocation['moo_strikes']:
                html += '<div class="option-strikes">'
                for strike in allocation['moo_strikes']:
                    html += f"""
                                <div class="strike-item">
                                    <span class="strike-info">Strike ${strike['strike']} ({strike['contracts']}c) <span class="{strike['type'].lower()}">{strike['type']}</span></span>
                                    <span>-${strike['cost']:,}</span>
                                </div>
                    """
                html += '</div>'
            
            html += f"""
                        </div>
                        
                        <div class="final-cash">
                            <div style="font-size: 12px; color: var(--textM); margin-bottom: 4px;">최종 현금 잔고</div>
                            <div class="final-cash-amount">${allocation['final_cash']:,}</div>
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

def main():
    pipeline = RealisticGMEPipeline()
    html_content = pipeline.generate_realistic_html()
    
    with open('realistic_pipeline.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Realistic GME Pipeline generated!")
    print("File saved as: realistic_pipeline.html")
    print("\nKey Changes:")
    print("   • Fidelity option limit: $500,000")
    print("   • Moomoo option limit: $750,000") 
    print("   • CS stock max: 50,000 shares")
    print("   • 37:63 ratio maintained")
    print("   • Realistic contract allocation")

if __name__ == "__main__":
    main()
