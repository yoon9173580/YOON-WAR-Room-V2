import requests
import time
from datetime import datetime
import json

class UltraRealisticGMEPipeline:
    def __init__(self):
        self.base_gme_price = 25.00
        self.price_cache = {}
        self.cache_timeout = 300  # 5 minutes cache
        
        # 초현실적 리테일 제약사항 (Block Trade 불가)
        self.ultra_realistic_constraints = {
            'cs_shares_target': 100000,      # CS 현물: 10만주 (가능)
            'fid_max_option_size': 200000,   # Fidelity 옵션: $20만 한도 (극도로 제한)
            'moo_max_option_size': 300000,   # Moomoo 옵션: $30만 한도 (극도로 제한)
            'max_contracts_per_strike': 200, # 스트라이크당 최대 200컨트랙트 (리테일 한계)
            'option_strikes': [20, 25, 30, 35, 40],  # 현실적인 스트라이크
            'daily_option_limit': 50000,     # 일일 옵션 구매 한도
            'liquidity_constraint': True      # 유동성 제약사항 적용
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
    
    def calculate_ultra_realistic_allocations(self):
        """초현실적 리테일 제약사항을 반영한 자금 배분"""
        current_price = self.get_gme_price()
        allocations = []
        
        for i, st1_total in enumerate(self.st1_totals):
            # ST 2 집행 후 잔액
            st2_remaining = st1_total - self.st2_total
            
            # CS 현물: 10만주 목표 (가능한 범위 내에서)
            cs_shares = min(self.ultra_realistic_constraints['cs_shares_target'], 
                           int(st2_remaining / current_price))
            cs_cost = cs_shares * current_price
            cs_remaining = st2_remaining - cs_cost
            
            # Fidelity 옵션: 극도로 제한된 금액만
            fid_option_amount = min(self.ultra_realistic_constraints['fid_max_option_size'], 
                                   min(cs_remaining, self.ultra_realistic_constraints['daily_option_limit']))
            fid_remaining = cs_remaining - fid_option_amount
            
            # Moomoo 옵션: 역시 극도로 제한
            moo_option_amount = min(self.ultra_realistic_constraints['moo_max_option_size'], 
                                   min(fid_remaining, self.ultra_realistic_constraints['daily_option_limit']))
            final_cash = fid_remaining - moo_option_amount
            
            # 옵션 스트라이크별 분배 (리테일 현실성 극대화)
            fid_strikes = self.allocate_ultra_conservative_options(fid_option_amount, current_price)
            moo_strikes = self.allocate_ultra_conservative_options(moo_option_amount, current_price)
            
            allocation = {
                'scenario': i + 1,
                'st1_total': st1_total,
                'st2_total': self.st2_total,
                'st2_remaining': st2_remaining,
                'cs_shares': cs_shares,
                'cs_cost': cs_cost,
                'cs_remaining': cs_remaining,
                'fid_option_total': fid_option_amount,
                'fid_strikes': fid_strikes,
                'fid_remaining': fid_remaining,
                'moo_option_total': moo_option_amount,
                'moo_strikes': moo_strikes,
                'final_cash': final_cash,
                'gme_price': current_price,
                'option_utilization_rate': (fid_option_amount + moo_option_amount) / cs_remaining if cs_remaining > 0 else 0
            }
            
            allocations.append(allocation)
            
        return allocations
    
    def allocate_ultra_conservative_options(self, total_amount, current_price):
        """초보수적 옵션 할당 (리테일 현실성 극대화)"""
        strikes = []
        remaining_amount = total_amount
        
        # ATM 근처의 스트라이크만 선택 (유동성 좋은 것)
        atm_strikes = [strike for strike in self.ultra_realistic_constraints['option_strikes'] 
                      if abs(strike - current_price) <= 10]
        
        if not atm_strikes:
            atm_strikes = [self.ultra_realistic_constraints['option_strikes'][2]]  # 기본값
        
        # 각 스트라이크에 소량만 분배
        per_strike_budget = min(remaining_amount // len(atm_strikes), 
                               self.ultra_realistic_constraints['max_contracts_per_strike'] * 500)  # 컨트랙트당 최대 $500
        
        for strike in atm_strikes:
            if remaining_amount <= 0:
                break
                
            # 보수적인 프리미엄 추정
            intrinsic_value = max(0, current_price - strike)
            time_value = 1.5  # 낮은 시간가치 (보수적)
            premium_per_contract = (intrinsic_value + time_value) * 100
            
            # 매우 적은 컨트랙트 수만
            max_contracts = min(
                self.ultra_realistic_constraints['max_contracts_per_strike'],
                int(per_strike_budget / premium_per_contract) if premium_per_contract > 0 else 0,
                50  # 추가 제약: 스트라이크당 최대 50컨트랙트
            )
            
            if max_contracts > 0:
                contract_cost = max_contracts * premium_per_contract
                strikes.append({
                    'strike': strike,
                    'contracts': max_contracts,
                    'cost': contract_cost,
                    'type': 'ITM' if current_price > strike else 'OTM',
                    'liquidity': 'Good' if abs(strike - current_price) <= 5 else 'Limited'
                })
                remaining_amount -= contract_cost
        
        return strikes
    
    def generate_ultra_realistic_html(self):
        """초현실적 파이프라인 HTML 생성"""
        allocations = self.calculate_ultra_realistic_allocations()
        current_price = self.get_gme_price()
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>YOON MASTER COMMAND — Ultra-Realistic GME Pipeline V56</title>
            <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg: #05070a;
                    --bg2: #0b0f15;
                    --bg3: #10151d;
                    --bg4: #141b25;
                    --border: rgba(255, 255, 255, 0.07);
                    --borderB: rgba(255, 255, 255, 0.13);
                    --text: #dde6f0;
                    --textM: #8899aa;
                    --textD: #3d5068;
                    --accent: #00d4aa;
                    --amber: #f59e0b;
                    --bull: #22d45a;
                    --bear: #f04040;
                    --purple: #a78bfa;
                    --red: #ef4444;
                    --orange: #f97316;
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
                
                .reality-check {{
                    background: rgba(249, 115, 22, 0.1);
                    border: 1px solid rgba(249, 115, 22, 0.3);
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 24px;
                }}
                
                .reality-check h3 {{
                    color: var(--orange);
                    margin-bottom: 12px;
                    font-size: 16px;
                }}
                
                .reality-explanation {{
                    font-size: 12px;
                    color: var(--textM);
                    margin-bottom: 12px;
                    line-height: 1.5;
                }}
                
                .constraints-list {{
                    list-style: none;
                    font-size: 12px;
                    color: var(--textM);
                }}
                
                .constraints-list li {{
                    padding: 4px 0;
                    display: flex;
                    align-items: center;
                }}
                
                .constraint-icon {{
                    color: var(--orange);
                    margin-right: 8px;
                }}
                
                .scenario-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
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
                .warning {{ color: var(--orange); }}
                
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
                
                .liquidity-good {{ color: var(--accent); }}
                .liquidity-limited {{ color: var(--orange); }}
                
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
                
                .option-utilization {{
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 4px;
                    padding: 8px;
                    margin-top: 8px;
                    text-align: center;
                }}
                
                .utilization-rate {{
                    font-size: 11px;
                    color: var(--red);
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
                    <div class="subtitle">Ultra-Realistic GME Pipeline V56 — No Block Trades</div>
                </div>
                
                <div class="price-banner">
                    <div class="current-price">GME: ${current_price:.2f}</div>
                    <div style="font-size: 12px; color: var(--textM); margin-top: 4px;">
                        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
                
                <div class="reality-check">
                    <h3>🚨 RETAIL REALITY CHECK</h3>
                    <div class="reality-explanation">
                        "현물 10만주는 가능하지만, 리테일에서 옵션 대량 구매는 Block Trade 없이 거의 불가능합니다. 
                        기관이 아닌 이상 유동성과 브로커 제약으로 인해 극소량만 구매할 수 있습니다."
                    </div>
                    <ul class="constraints-list">
                        <li><span class="constraint-icon">•</span>CS 현물: 100,000주 (가능 - Computershare)</li>
                        <li><span class="constraint-icon">•</span>Fidelity 옵션: 최대 $200,000 (리테일 한계)</li>
                        <li><span class="constraint-icon">•</span>Moomoo 옵션: 최대 $300,000 (리테일 한계)</li>
                        <li><span class="constraint-icon">•</span>스트라이크당: 최대 200컨트랙트 (극도 제한)</li>
                        <li><span class="constraint-icon">•</span>일일 한도: $50,000 (리스크 관리)</li>
                        <li><span class="constraint-icon">•</span>유동성: ATM 근처만 가능</li>
                    </ul>
                </div>
                
                <div class="scenario-grid">
        """
        
        # 각 시나리오별 카드 생성
        for allocation in allocations:
            utilization_pct = allocation['option_utilization_rate'] * 100
            
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
                            <div class="allocation-title">ST 3. 초현실적 GME 투입</div>
                            <div class="allocation-item">
                                <span class="allocation-label">CS 현물 ({allocation['cs_shares']:,}주):</span>
                                <span class="allocation-value neg">-${allocation['cs_cost']:,}</span>
                            </div>
                            <div class="allocation-item">
                                <span class="allocation-label">Fidelity 옵션 (극소량):</span>
                                <span class="allocation-value neg">-${allocation['fid_option_total']:,}</span>
                            </div>
            """
            
            # Fidelity 스트라이크 상세
            if allocation['fid_strikes']:
                html += '<div class="option-strikes">'
                for strike in allocation['fid_strikes']:
                    liquidity_class = f"liquidity-{strike['liquidity'].lower()}"
                    html += f"""
                                <div class="strike-item">
                                    <span class="strike-info">Strike ${strike['strike']} ({strike['contracts']}c) 
                                        <span class="{strike['type'].lower()}">{strike['type']}</span> 
                                        <span class="{liquidity_class}">{strike['liquidity']}</span>
                                    </span>
                                    <span>-${strike['cost']:,}</span>
                                </div>
                    """
                html += '</div>'
            
            html += f"""
                            <div class="allocation-item">
                                <span class="allocation-label">Moomoo 옵션 (극소량):</span>
                                <span class="allocation-value neg">-${allocation['moo_option_total']:,}</span>
                            </div>
            """
            
            # Moomoo 스트라이크 상세
            if allocation['moo_strikes']:
                html += '<div class="option-strikes">'
                for strike in allocation['moo_strikes']:
                    liquidity_class = f"liquidity-{strike['liquidity'].lower()}"
                    html += f"""
                                <div class="strike-item">
                                    <span class="strike-info">Strike ${strike['strike']} ({strike['contracts']}c) 
                                        <span class="{strike['type'].lower()}">{strike['type']}</span> 
                                        <span class="{liquidity_class}">{strike['liquidity']}</span>
                                    </span>
                                    <span>-${strike['cost']:,}</span>
                                </div>
                    """
                html += '</div>'
            
            html += f"""
                        </div>
                        
                        <div class="option-utilization">
                            <div class="utilization-rate">
                                옵션 활용률: {utilization_pct:.1f}% (리테일 한계로 인해 극히 낮음)
                            </div>
                        </div>
                        
                        <div class="final-cash">
                            <div style="font-size: 12px; color: var(--textM); margin-bottom: 4px;">최종 현금 잔고 (대부분 현금 유지)</div>
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
    pipeline = UltraRealisticGMEPipeline()
    html_content = pipeline.generate_ultra_realistic_html()
    
    with open('ultra_realistic_pipeline.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Ultra-Realistic GME Pipeline generated!")
    print("File saved as: ultra_realistic_pipeline.html")
    print("\nUltra-Realistic Constraints Applied:")
    print("   • CS Stock: 100,000 shares (possible)")
    print("   • Fidelity Options: Max $200,000 (retail limit)")
    print("   • Moomoo Options: Max $300,000 (retail limit)")
    print("   • Contracts per strike: Max 200 (extremely limited)")
    print("   • Daily option limit: $50,000")
    print("   • No block trades - retail reality")

if __name__ == "__main__":
    main()
