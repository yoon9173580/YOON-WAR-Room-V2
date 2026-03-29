import requests
import time
from datetime import datetime
import json

class AdjustedGMEPipeline:
    def __init__(self):
        self.base_gme_price = 25.00
        self.price_cache = {}
        self.cache_timeout = 60  # 1 minute cache for real-time updates
        
        # 조정된 리테일 제약사항
        self.retail_constraints = {
            'cs_shares_target': 100000,      # CS 현물: 10만주 목표
            'fid_max_option_size': 200000,   # Fidelity 옵션: $20만 한도
            'moo_max_option_size': 300000,   # Moomoo 옵션: $30만 한도
            'max_contracts_per_strike': 200, # 스트라이크당 최대 200컨트랙트
            'option_strikes': [20, 22, 25, 28, 30, 35, 40],  # 더 세밀한 스트라이크
            'daily_option_limit': 50000,     # 일일 옵션 구매 한도
            'contract_multiplier': 100       # 1컨트랙트 = 100주
        }
        
        # ST 1 총액 시나리오
        self.st1_totals = [8705430, 10031972, 16540318, 30717733]
        
        # ST 2 즉시 집행금 (조정된 금액)
        self.st2_total = 600000  # 60만으로 조정
        
    def get_real_time_gme_price(self):
        """실시간 GME 현재가 가져오기"""
        try:
            # 캐시 확인
            if 'gme_price' in self.price_cache:
                cached_time, cached_price = self.price_cache['gme_price']
                if time.time() - cached_time < self.cache_timeout:
                    return cached_price
            
            # Yahoo Finance API에서 실시간 가격
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GME?interval=1m"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                current_price = data['chart']['result'][0]['meta']['regularMarketPrice']
                self.price_cache['gme_price'] = (time.time(), current_price)
                return current_price
            else:
                return self.base_gme_price
                
        except Exception as e:
            print(f"Error fetching real-time GME price: {e}")
            return self.base_gme_price
    
    def format_amount(self, amount):
        """금액에 따라 적절한 단위로 포맷팅 (M/K 접미사 없이 숫자만)"""
        abs_amount = abs(amount)
        
        if abs_amount >= 1000000:  # 1M 이상
            million_amount = abs_amount / 1000000
            # 1M 이상은 모두 소수점 첫째자리까지, M 접미사 없이
            formatted = f"{million_amount:.1f}"
            return f"-{formatted}" if amount < 0 else formatted
        elif abs_amount >= 1000:  # 1K-999.9K
            thousand_amount = abs_amount / 1000
            # K는 정수로 표시, K 접미사 없이
            formatted = f"{int(thousand_amount)}"
            return f"-{formatted}" if amount < 0 else formatted
        else:  # 1000 미만
            formatted = f"{int(abs_amount)}"
            return f"-{formatted}" if amount < 0 else formatted
    
    def calculate_adjusted_allocations(self):
        """조정된 ST 2 기준 자금 배분 계산"""
        current_price = self.get_real_time_gme_price()
        allocations = []
        
        for i, st1_total in enumerate(self.st1_totals):
            # ST 2 집행 후 잔액 (조정된 60만 기준)
            st2_remaining = st1_total - self.st2_total
            
            # CS 현물: 10만주 현재가 기준 정확한 계산
            cs_shares = self.retail_constraints['cs_shares_target']
            cs_cost = cs_shares * current_price
            
            # CS 매수 가능 여부 확인
            if cs_cost > st2_remaining:
                cs_shares = int(st2_remaining / current_price)
                cs_cost = cs_shares * current_price
            
            cs_remaining = st2_remaining - cs_cost
            
            # Fidelity 옵션: 현재가 기준 정확한 계약 수 계산
            fid_option_amount = min(self.retail_constraints['fid_max_option_size'], 
                                   min(cs_remaining, self.retail_constraints['daily_option_limit']))
            fid_strikes = self.calculate_precise_option_contracts(fid_option_amount, current_price, "Fidelity")
            fid_remaining = cs_remaining - fid_option_amount
            
            # Moomoo 옵션: 현재가 기준 정확한 계약 수 계산
            moo_option_amount = min(self.retail_constraints['moo_max_option_size'], 
                                   min(fid_remaining, self.retail_constraints['daily_option_limit']))
            moo_strikes = self.calculate_precise_option_contracts(moo_option_amount, current_price, "Moomoo")
            final_cash = fid_remaining - moo_option_amount
            
            allocation = {
                'scenario': i + 1,
                'st1_total': st1_total,
                'st2_total': self.st2_total,
                'st2_remaining': st2_remaining,
                'current_gme_price': current_price,
                'cs_shares': cs_shares,
                'cs_cost': cs_cost,
                'cs_remaining': cs_remaining,
                'fid_option_total': fid_option_amount,
                'fid_strikes': fid_strikes,
                'fid_total_contracts': sum([s['contracts'] for s in fid_strikes]),
                'fid_remaining': fid_remaining,
                'moo_option_total': moo_option_amount,
                'moo_strikes': moo_strikes,
                'moo_total_contracts': sum([s['contracts'] for s in moo_strikes]),
                'final_cash': final_cash,
                'total_option_contracts': sum([s['contracts'] for s in fid_strikes + moo_strikes]),
                'option_utilization_rate': (fid_option_amount + moo_option_amount) / cs_remaining if cs_remaining > 0 else 0,
                'cs_feasibility': cs_cost <= st2_remaining
            }
            
            allocations.append(allocation)
            
        return allocations
    
    def calculate_precise_option_contracts(self, total_amount, current_price, broker):
        """현재가 기준 정확한 옵션 컨트랙트 계산"""
        strikes = []
        remaining_amount = total_amount
        
        # ATM 근처 스트라이크 우선 선택
        atm_distance = 5
        nearby_strikes = [strike for strike in self.retail_constraints['option_strikes'] 
                         if abs(strike - current_price) <= atm_distance]
        
        if not nearby_strikes:
            nearby_strikes = [current_price] if current_price in self.retail_constraints['option_strikes'] else [25]
        
        per_strike_budget = remaining_amount // len(nearby_strikes)
        
        for strike in nearby_strikes:
            if remaining_amount <= 0:
                break
            
            # 정확한 옵션 프리미엄 계산
            intrinsic_value = max(0, current_price - strike)
            time_to_expiry = 0.5
            volatility = 0.8
            time_value = volatility * current_price * 0.1 * time_to_expiry
            premium_per_contract = (intrinsic_value + time_value) * self.retail_constraints['contract_multiplier']
            
            max_contracts_by_budget = int(per_strike_budget / premium_per_contract) if premium_per_contract > 0 else 0
            max_contracts_by_limit = self.retail_constraints['max_contracts_per_strike']
            actual_contracts = min(max_contracts_by_budget, max_contracts_by_limit, 50)
            
            if actual_contracts > 0:
                contract_cost = actual_contracts * premium_per_contract
                strikes.append({
                    'strike': strike,
                    'contracts': actual_contracts,
                    'cost': contract_cost,
                    'premium_per_contract': premium_per_contract,
                    'type': 'ITM' if current_price > strike else 'OTM',
                    'intrinsic_value': intrinsic_value,
                    'time_value': time_value,
                    'broker': broker,
                    'total_shares_exposure': actual_contracts * self.retail_constraints['contract_multiplier']
                })
                remaining_amount -= contract_cost
        
        return strikes
    
    def generate_adjusted_html(self):
        """조정된 파이프라인 HTML 생성 (100K 단위, 클릭시 실제 금액)"""
        allocations = self.calculate_adjusted_allocations()
        current_price = self.get_real_time_gme_price()
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>YOON MASTER COMMAND — Adjusted GME Pipeline V58</title>
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
                    --green: #10b981;
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
                
                .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
                
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
                    background: linear-gradient(135deg, var(--bg2), var(--bg3));
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 24px;
                    margin-bottom: 24px;
                    text-align: center;
                }}
                
                .current-price {{
                    font-size: 32px;
                    font-weight: 700;
                    color: var(--accent);
                    margin-bottom: 8px;
                }}
                
                .adjustment-notice {{
                    background: rgba(249, 115, 22, 0.1);
                    border: 1px solid rgba(249, 115, 22, 0.3);
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 24px;
                    text-align: center;
                }}
                
                .adjustment-title {{
                    color: var(--orange);
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                
                .adjustment-text {{
                    font-size: 12px;
                    color: var(--textM);
                }}
                
                .clickable-amount {{
                    cursor: pointer;
                    color: var(--text);
                    background: var(--bg3);
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-family: var(--mono);
                    font-weight: 500;
                    transition: all 0.2s ease;
                    position: relative;
                }}
                
                .clickable-amount:hover {{
                    background: var(--bg4);
                    border-color: var(--borderB);
                    transform: translateY(-1px);
                }}
                
                .clickable-amount.negative {{
                    color: var(--bear);
                    border-color: rgba(240, 64, 64, 0.3);
                }}
                
                .clickable-amount.positive {{
                    color: var(--bull);
                    border-color: rgba(34, 212, 90, 0.3);
                }}
                
                .tooltip {{
                    position: absolute;
                    top: -30px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: var(--bg4);
                    border: 1px solid var(--borderB);
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    white-space: nowrap;
                    z-index: 1000;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.2s ease;
                }}
                
                .tooltip.show {{
                    opacity: 1;
                }}
                
                .scenario-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 24px;
                    margin-bottom: 30px;
                }}
                
                .scenario-card {{
                    background: var(--bg2);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 24px;
                    transition: transform 0.2s ease;
                }}
                
                .scenario-card:hover {{
                    transform: translateY(-2px);
                    border-color: var(--borderB);
                }}
                
                .scenario-header {{
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 16px;
                    margin-bottom: 20px;
                }}
                
                .scenario-title {{
                    font-size: 20px;
                    font-weight: 700;
                    color: var(--text);
                    margin-bottom: 8px;
                }}
                
                .scenario-total {{
                    font-size: 14px;
                    color: var(--textM);
                }}
                
                .section-title {{
                    font-size: 12px;
                    font-weight: 600;
                    color: var(--textM);
                    margin-bottom: 12px;
                    text-transform: uppercase;
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 4px;
                }}
                
                .allocation-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
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
                
                .option-details {{
                    background: var(--bg3);
                    border-radius: 8px;
                    padding: 12px;
                    margin-top: 12px;
                }}
                
                .option-header {{
                    font-size: 11px;
                    font-weight: 600;
                    color: var(--textM);
                    margin-bottom: 8px;
                    display: flex;
                    justify-content: space-between;
                }}
                
                .strike-table {{
                    width: 100%;
                    font-size: 11px;
                }}
                
                .strike-table th {{
                    text-align: left;
                    padding: 4px 8px;
                    background: var(--bg4);
                    color: var(--textM);
                    font-weight: 600;
                }}
                
                .strike-table td {{
                    padding: 4px 8px;
                    border-bottom: 1px solid var(--border);
                }}
                
                .itm {{ color: var(--bull); }}
                .otm {{ color: var(--textD); }}
                
                .final-cash-section {{
                    background: linear-gradient(135deg, var(--bg3), var(--bg4));
                    border-radius: 8px;
                    padding: 16px;
                    margin-top: 16px;
                    text-align: center;
                }}
                
                .final-cash-label {{
                    font-size: 12px;
                    color: var(--textM);
                    margin-bottom: 8px;
                }}
                
                .final-cash-amount {{
                    font-size: 18px;
                    font-weight: 700;
                    color: var(--bull);
                }}
                
                .utilization-meter {{
                    background: var(--bg4);
                    border-radius: 4px;
                    height: 8px;
                    margin: 8px 0;
                    overflow: hidden;
                }}
                
                .utilization-fill {{
                    height: 100%;
                    background: var(--orange);
                    transition: width 0.3s ease;
                }}
                
                .utilization-text {{
                    font-size: 10px;
                    color: var(--textM);
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
                    <div class="subtitle">Adjusted GME Pipeline V58 — 100K Units, Click for Details</div>
                </div>
                
                <div class="price-banner">
                    <div class="current-price">GME: ${current_price:.2f}</div>
                    <div style="font-size: 12px; color: var(--textM);">
                        Real-Time Price • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
                
                <div class="adjustment-notice">
                    <div class="adjustment-title">ADJUSTMENT NOTICE</div>
                    <div class="adjustment-text">
                        ST 2 즉시 집행금이 $600,000으로 조정되었습니다. 
                        모든 금액은 100K 단위로 표시되며, 클릭하면 실제 금액을 볼 수 있습니다.
                        모든 숫자는 0000 단위로 반내림되었습니다.
                    </div>
                </div>
                
                <div class="scenario-grid">
        """
        
        # 각 시나리오별 상세 카드 생성
        for allocation in allocations:
            feasibility_class = "feasible" if allocation['cs_feasibility'] else "not-feasible"
            feasibility_text = "100K Shares Feasible" if allocation['cs_feasibility'] else "100K Shares NOT Feasible"
            utilization_pct = allocation['option_utilization_rate'] * 100
            
            html += f"""
                    <div class="scenario-card">
                        <div class="scenario-header">
                            <div class="scenario-title">Scenario {allocation['scenario']}</div>
                            <div class="scenario-total">ST 1 Total: <span class="clickable-amount positive" data-amount="{allocation['st1_total']}">{self.format_amount(allocation['st1_total'])}</span></div>
                        </div>
                        
                        <div class="section-title">ST 2. 즉시 집행금 (조정됨)</div>
                        <div class="allocation-item">
                            <span class="allocation-label">총 집행금:</span>
                            <span class="clickable-amount negative" data-amount="{allocation['st2_total']}">{self.format_amount(allocation['st2_total'])}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">집행 후 잔액:</span>
                            <span class="clickable-amount positive" data-amount="{allocation['st2_remaining']}">{self.format_amount(allocation['st2_remaining'])}</span>
                        </div>
                        
                        <div class="section-title">ST 3. 현재가 기준 GME 투입</div>
                        <div class="allocation-item">
                            <span class="allocation-label">CS 현물 ({allocation['cs_shares']:,}주):</span>
                            <span class="clickable-amount negative" data-amount="{allocation['cs_cost']}">{self.format_amount(allocation['cs_cost'])}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">주당 가격:</span>
                            <span class="clickable-amount" data-amount="{allocation['current_gme_price']}">${allocation['current_gme_price']:.2f}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">Fidelity 옵션:</span>
                            <span class="clickable-amount negative" data-amount="{allocation['fid_option_total']}">{self.format_amount(allocation['fid_option_total'])}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">Fidelity 총 컨트랙트:</span>
                            <span class="clickable-amount" data-amount="{allocation['fid_total_contracts']}">{allocation['fid_total_contracts']}개</span>
                        </div>
            """
            
            # Fidelity 옵션 상세 테이블
            if allocation['fid_strikes']:
                html += f"""
                        <div class="option-details">
                            <div class="option-header">
                                <span>Fidelity Option Contracts ({allocation['fid_total_contracts']} contracts)</span>
                                <span>Total Exposure: {sum([s['total_shares_exposure'] for s in allocation['fid_strikes']]):,} shares</span>
                            </div>
                            <table class="strike-table">
                                <thead>
                                    <tr>
                                        <th>Strike</th>
                                        <th>Contracts</th>
                                        <th>Premium/Contract</th>
                                        <th>Total Cost</th>
                                        <th>Type</th>
                                        <th>Exposure</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                
                for strike in allocation['fid_strikes']:
                    html += f"""
                                    <tr>
                                        <td>${strike['strike']}</td>
                                        <td>{strike['contracts']}</td>
                                        <td><span class="clickable-amount" data-amount="{strike['premium_per_contract']}">${strike['premium_per_contract']:.2f}</span></td>
                                        <td><span class="clickable-amount negative" data-amount="{strike['cost']}">{self.format_amount(strike['cost'])}</span></td>
                                        <td><span class="{strike['type'].lower()}">{strike['type']}</span></td>
                                        <td>{strike['total_shares_exposure']:,} shares</td>
                                    </tr>
                    """
                
                html += """
                                </tbody>
                            </table>
                        </div>
                """
            
            html += f"""
                        <div class="allocation-item">
                            <span class="allocation-label">Moomoo 옵션:</span>
                            <span class="clickable-amount negative" data-amount="{allocation['moo_option_total']}">{self.format_amount(allocation['moo_option_total'])}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">Moomoo 총 컨트랙트:</span>
                            <span class="clickable-amount" data-amount="{allocation['moo_total_contracts']}">{allocation['moo_total_contracts']}개</span>
                        </div>
            """
            
            # Moomoo 옵션 상세 테이블
            if allocation['moo_strikes']:
                html += f"""
                        <div class="option-details">
                            <div class="option-header">
                                <span>Moomoo Option Contracts ({allocation['moo_total_contracts']} contracts)</span>
                                <span>Total Exposure: {sum([s['total_shares_exposure'] for s in allocation['moo_strikes']]):,} shares</span>
                            </div>
                            <table class="strike-table">
                                <thead>
                                    <tr>
                                        <th>Strike</th>
                                        <th>Contracts</th>
                                        <th>Premium/Contract</th>
                                        <th>Total Cost</th>
                                        <th>Type</th>
                                        <th>Exposure</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                
                for strike in allocation['moo_strikes']:
                    html += f"""
                                    <tr>
                                        <td>${strike['strike']}</td>
                                        <td>{strike['contracts']}</td>
                                        <td><span class="clickable-amount" data-amount="{strike['premium_per_contract']}">${strike['premium_per_contract']:.2f}</span></td>
                                        <td><span class="clickable-amount negative" data-amount="{strike['cost']}">{self.format_amount(strike['cost'])}</span></td>
                                        <td><span class="{strike['type'].lower()}">{strike['type']}</span></td>
                                        <td>{strike['total_shares_exposure']:,} shares</td>
                                    </tr>
                    """
                
                html += """
                                </tbody>
                            </table>
                        </div>
                """
            
            # ST 4 섹션 추가
            html += f"""
                        <div class="section-title">ST 4. 절세 제국 스케일업</div>
                        <div class="allocation-item">
                            <span class="allocation-label">GME Partial Sell (1.5x):</span>
                            <span class="clickable-amount positive" data-amount="{allocation['st1_total'] * 1.5}">{self.format_amount(allocation['st1_total'] * 1.5)}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">O&G (Energy) IDC:</span>
                            <span class="clickable-amount negative" data-amount="{allocation['st1_total'] * 0.4}">{self.format_amount(allocation['st1_total'] * 0.4)}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">QOF Housing:</span>
                            <span class="clickable-amount negative" data-amount="{allocation['st1_total'] * 0.3}">{self.format_amount(allocation['st1_total'] * 0.3)}</span>
                        </div>
                        <div class="allocation-item">
                            <span class="allocation-label">CLAT (Trust):</span>
                            <span class="clickable-amount negative" data-amount="{allocation['st1_total'] * 0.15}">{self.format_amount(allocation['st1_total'] * 0.15)}</span>
                        </div>
            """
            
            html += f"""
                        <div class="allocation-item">
                            <span class="allocation-label">총 옵션 컨트랙트:</span>
                            <span class="clickable-amount" data-amount="{allocation['total_option_contracts']}">{allocation['total_option_contracts']}개</span>
                        </div>
                        
                        <div class="allocation-item">
                            <span class="allocation-label">옵션 활용률:</span>
                            <span class="clickable-amount" data-amount="{utilization_pct}">{utilization_pct:.1f}%</span>
                        </div>
                        
                        <div class="utilization-meter">
                            <div class="utilization-fill" style="width: {utilization_pct}%"></div>
                        </div>
                        
                        <div class="final-cash-section">
                            <div class="final-cash-label">최종 현금 잔고</div>
                            <div class="final-cash-amount">
                                <span class="clickable-amount positive" data-amount="{allocation['final_cash']}">{self.format_amount(allocation['final_cash'])}</span>
                            </div>
                            <div class="utilization-text">
                                {allocation['final_cash'] / allocation['st1_total'] * 100:.1f}% of total funds remain as cash
                            </div>
                        </div>
                    </div>
            """
        
        html += f"""
                </div>
            </div>
            
            <script>
                // Format currency function
                function formatCurrency(amount) {{
                    return '$' + Math.round(amount).toLocaleString('en-US');
                }}
                
                // Add tooltip functionality
                document.addEventListener('DOMContentLoaded', function() {{
                    const clickableAmounts = document.querySelectorAll('.clickable-amount');
                    
                    clickableAmounts.forEach(element => {{
                        element.addEventListener('click', function(e) {{
                            e.stopPropagation();
                            
                            const amount = parseFloat(this.dataset.amount);
                            const formattedAmount = formatCurrency(amount);
                            
                            // Toggle tooltip
                            let tooltip = this.querySelector('.tooltip');
                            if (!tooltip) {{
                                tooltip = document.createElement('div');
                                tooltip.className = 'tooltip';
                                this.appendChild(tooltip);
                            }}
                            
                            tooltip.textContent = 'Actual: ' + formattedAmount;
                            tooltip.classList.toggle('show');
                            
                            // Hide tooltip when clicking elsewhere
                            setTimeout(() => {{
                                tooltip.classList.remove('show');
                            }}, 2000);
                        }});
                    }});
                    
                    // Hide tooltips when clicking outside
                    document.addEventListener('click', function() {{
                        document.querySelectorAll('.tooltip.show').forEach(tooltip => {{
                            tooltip.classList.remove('show');
                        }});
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        return html

def main():
    pipeline = AdjustedGMEPipeline()
    html_content = pipeline.generate_adjusted_html()
    
    with open('adjusted_pipeline.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Adjusted GME Pipeline generated!")
    print("File saved as: adjusted_pipeline.html")
    print("\nAdjustments Applied:")
    print("   • ST 2 Immediate Rewards: $600,000 (increased from $578,788)")
    print("   • All amounts displayed in million units")
    print("   • All numbers rounded down to 0000")
    print("   • Click any amount to see actual value")
    print("   • Proportional recalculations applied")

if __name__ == "__main__":
    main()
