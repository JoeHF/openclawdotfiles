#!/usr/bin/env python3
"""
Investment Advisor Technical Analysis - Tushare Version
数据源: Tushare API
"""

import tushare as ts
import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd

def get_pro():
    """获取Tushare Pro API实例"""
    token = os.getenv('TUSHARE_TOKEN') 
    if not token:
        # Try to get from OpenClaw config
        try:
            with open(os.path.expanduser('~/.openclaw/openclaw.json')) as f:
                import json
                config = json.load(f)
                token = config.get('env', {}).get('TUSHARE_TOKEN', '')
        except:
            pass
    
    if not token:
        return None
    return ts.pro_api(token)

def fetch_kline_data(pro, symbol, days=60):
    """获取K线数据"""
    # 转换代码格式
    if symbol.startswith('6'):
        ts_code = f"{symbol}.SH"
    elif symbol.startswith('0') or symbol.startswith('3'):
        ts_code = f"{symbol}.SZ"
    else:
        ts_code = symbol
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')
    
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        df = df.sort_values('trade_date')
        return df
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        return None

def get_latest_price(pro, symbol):
    """获取最新价格"""
    if symbol.startswith('6'):
        ts_code = f"{symbol}.SH"
    elif symbol.startswith('0') or symbol.startswith('3'):
        ts_code = f"{symbol}.SZ"
    else:
        ts_code = symbol
    
    try:
        df = pro.daily(ts_code=ts_code, start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'))
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            return {
                'price': float(latest['close']),
                'pre_close': float(prev['close']),
                'pct_chg': float(latest['pct_chg']),
                'open': float(latest['open']),
                'high': float(latest['high']),
                'low': float(latest['low']),
                'volume': float(latest['vol']),
                'amount': float(latest['amount'])
            }
    except Exception as e:
        print(f"Error getting price: {e}", file=sys.stderr)
    return None

def calculate_ma(df, periods=[5, 10, 20]):
    """计算移动平均线"""
    result = {}
    close = df['close'].astype(float)
    for period in periods:
        ma = close.rolling(period).mean()
        if not pd.isna(ma.iloc[-1]):  # Check for NaN
            result[f'ma{period}'] = round(ma.iloc[-1], 2)
    return result

def calculate_rsi(df, period=14):
    """计算RSI指标"""
    close = df['close'].astype(float)
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    
    if avg_loss.iloc[-1] == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi.iloc[-1], 2)

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    close = df['close'].astype(float)
    
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    macd = (dif - dea) * 2
    
    return {
        'dif': round(dif.iloc[-1], 4),
        'dea': round(dea.iloc[-1], 4),
        'macd': round(macd.iloc[-1], 4)
    }

def calculate_bollinger(df, period=20, std_dev=2):
    """计算布林带"""
    close = df['close'].astype(float)
    
    ma = close.rolling(period).mean()
    std = close.rolling(period).std()
    
    upper = ma + (std * std_dev)
    lower = ma - (std * std_dev)
    
    return {
        'upper': round(upper.iloc[-1], 2),
        'middle': round(ma.iloc[-1], 2),
        'lower': round(lower.iloc[-1], 2)
    }

def analyze_technical(symbol, mode='full'):
    """技术分析主函数"""
    pro = get_pro()
    if not pro:
        return {'error': 'TUSHARE_TOKEN not found'}
    
    # 清理symbol
    symbol = symbol.replace('.SH', '').replace('.SZ', '')
    
    result = {'symbol': symbol}
    
    # 获取最新价格
    quote = get_latest_price(pro, symbol)
    if quote:
        result['quote'] = quote
        result['pct_chg'] = quote['pct_chg']
    
    # 获取K线数据
    df = fetch_kline_data(pro, symbol)
    if df is None or df.empty:
        return {'error': f'Cannot fetch data for {symbol}'}
    
    # 只取最近60天数据
    df = df.tail(60)
    
    # 计算技术指标
    if mode in ['full', 'technical']:
        result['ma'] = calculate_ma(df)
        result['rsi'] = calculate_rsi(df)
        result['macd'] = calculate_macd(df)
        result['bollinger'] = calculate_bollinger(df)
        
        # 简单趋势判断
        current_price = float(df['close'].iloc[-1])
        ma5 = result['ma'].get('ma5', current_price)
        ma10 = result['ma'].get('ma10', current_price)
        
        if current_price > ma5 > ma10:
            result['trend'] = 'bullish'
        elif current_price < ma5 < ma10:
            result['trend'] = 'bearish'
        else:
            result['trend'] = 'sideways'
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python technical_tushare.py <symbol> [mode]")
        sys.exit(1)
    
    symbol = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'full'
    
    result = analyze_technical(symbol, mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
