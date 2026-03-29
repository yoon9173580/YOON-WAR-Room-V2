import databento as db
import pandas as pd
import yfinance as yf
import datetime
import os
import re
import json

# 1. API 설정
DB_API_KEY = os.environ.get("DATABENTO_API_KEY") or "db-WDmvgkYYgMJhxBfAJpMybqbCM5hgj"
client = db.Historical(DB_API_KEY)
# 12번째 줄을 이렇게 수정하세요 (오늘 날짜에서 1일을 뺍니다)
date_target = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

print(f"🚀 [{date_target}] 모든 API 가동 및 데이터 믹싱 시작...")

try:
    # A. Yahoo Finance 엔진 (실시간 주가 및 변동성)
    tickers = yf.Tickers('SPY QQQ IWM ^VIX')
    spy_yf = tickers.tickers['SPY'].fast_info
    vix_yf = tickers.tickers['^VIX'].fast_info
    
    quotes = {
        "spy_p": spy_yf.last_price,
        "spy_chg": spy_yf.last_price - spy_yf.previous_close,
        "spy_pct": round((spy_yf.last_price / spy_yf.previous_close - 1) * 100, 2),
        "vix_p": vix_yf.last_price,
        "qqq_pct": (tickers.tickers['QQQ'].fast_info.last_price / tickers.tickers['QQQ'].fast_info.previous_close - 1) * 100,
        "iwm_pct": (tickers.tickers['IWM'].fast_info.last_price / tickers.tickers['IWM'].fast_info.previous_close - 1) * 100
    }

    # B. Databento 엔진 (정밀 VWAP 및 거래량 분석)
    # (애프터 마켓 포함 데이터 수집)
    target_dt = datetime.datetime.strptime(date_target, "%Y-%m-%d")
    next_day = (target_dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    db_data = client.timeseries.get_range(
        dataset="DBEQ.BASIC", schema="ohlcv-1m", symbols="SPY",
        start=f"{date_target}T13:30:00", end=f"{next_day}T00:00:00"
    )
    df = db_data.to_df()
    df_5m = df.resample('5min').agg({'high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    
    # VWAP 및 지표 계산
    tp = (df_5m['high'] + df_5m['low'] + df_5m['close']) / 3
    vwap = (df_5m['volume'] * tp).cumsum() / df_5m['volume'].cumsum()
    vol_sma = df_5m['volume'].rolling(window=20).mean()
    
    computed = {
        "vwap": vwap.iloc[-1],
        "vol_ratio": (df_5m['volume'].iloc[-1] / vol_sma.iloc[-1]) if vol_sma.iloc[-1] > 0 else 0,
        "range": f"${(df_5m['high'].max() - df_5m['low'].min()):.2f}",
        "gap": f"${(spy_yf.open - spy_yf.previous_close):.2f}",
        "prev_close": spy_yf.previous_close
    }

    # C. 최종 데이터 패키지 생성
    final_data = {**quotes, **computed}
    final_data["verdict"] = "STRONG GO" if final_data["vol_ratio"] > 1.5 and final_data["spy_p"] > final_data["vwap"] else "NO TRADE"

    # D. index.html에 주입
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 비밀 금고(py-data)에 JSON으로 저장
        json_str = json.dumps(final_data)
        content = re.sub(r'<script id="py-data">.*?</script>', 
                         f'<script id="py-data" type="application/json">\n{json_str}\n</script>', 
                         content, flags=re.DOTALL)
                         
        # ⬇️ 지금 멈추신 곳부터 이렇게 마저 작성해 주세요!
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("✅ index.html 데이터 주입 완료!")

# ⚠️ 중요: 아래 except는 파일 맨 왼쪽(들여쓰기 없이)에 맞춰야 합니다.
except Exception as e:
    print(f"❌ 에러 발생: {e}")
        