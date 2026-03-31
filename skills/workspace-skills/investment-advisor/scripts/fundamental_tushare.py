#!/usr/bin/env python3
"""
Investment Advisor Fundamental Analysis - Tushare Version
数据源: Tushare API
"""

import tushare as ts
import os
import sys
import json
from datetime import datetime, timedelta


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
        print("Error: TUSHARE_TOKEN not found. Please set environment variable.", file=sys.stderr)
        return None
    return ts.pro_api(token)

def format_symbol(symbol):
    """格式化股票代码"""
    symbol = symbol.replace('.SH', '').replace('.SZ', '')
    if symbol.startswith('6'):
        return f"{symbol}.SH"
    elif symbol.startswith('0') or symbol.startswith('3'):
        return f"{symbol}.SZ"
    return symbol

def get_stock_basic(pro, symbol):
    """获取股票基本信息"""
    ts_code = format_symbol(symbol)
    
    try:
        df = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,industry,market,list_date')
        if not df.empty:
            row = df.iloc[0]
            return {
                'name': row['name'],
                'industry': row.get('industry', ''),
                'market': row.get('market', ''),
                'list_date': row.get('list_date', '')
            }
    except Exception as e:
        print(f"Error getting basic info: {e}", file=sys.stderr)
    return None

def get_fina_indicator(pro, symbol, limit=4):
    """获取财务指标"""
    ts_code = format_symbol(symbol)
    
    try:
        df = pro.fina_indicator(ts_code=ts_code, limit=limit)
        if not df.empty:
            latest = df.iloc[0]
            return {
                'roe': float(latest.get('roe', 0)),
                'netprofit_margin': float(latest.get('netprofit_margin', 0)),
                'grossprofit_margin': float(latest.get('grossprofit_margin', 0)),
                'eps': float(latest.get('eps', 0)),
                'bvps': float(latest.get('bvps', 0)),
                'pe': float(latest.get('pe', 0)),
                'pb': float(latest.get('pb', 0)),
                'revenue_growth': float(latest.get('revenue_growth', 0)),
                'netprofit_growth': float(latest.get('netprofit_growth', 0))
            }
    except Exception as e:
        print(f"Error getting fina_indicator: {e}", file=sys.stderr)
    return None

def get_daily_basic(pro, symbol):
    """获取每日基本面数据"""
    ts_code = format_symbol(symbol)
    
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            latest = df.iloc[-1]
            return {
                'total_mv': float(latest.get('total_mv', 0)),
                'circ_mv': float(latest.get('circ_mv', 0)),
                'turnover_rate': float(latest.get('turnover_rate', 0))
            }
    except Exception as e:
        print(f"Error getting daily basic: {e}", file=sys.stderr)
    return None

def analyze_fundamental(symbol, mode='full'):
    """基本面分析主函数"""
    pro = get_pro()
    
    symbol = symbol.replace('.SH', '').replace('.SZ', '')
    
    result = {'symbol': symbol}
    
    basic = get_stock_basic(pro, symbol)
    if basic:
        result['basic'] = basic
    
    if mode in ['full', 'fundamental']:
        fina = get_fina_indicator(pro, symbol)
        if fina:
            result['financial'] = fina
            
            pe = fina.get('pe', 0)
            if pe and pe > 0:
                if pe < 20:
                    result['valuation'] = '低估'
                elif pe < 50:
                    result['valuation'] = '合理'
                elif pe > 100:
                    result['valuation'] = '高估'
                else:
                    result['valuation'] = '无法评估'
            elif pe == 0:
                result['valuation'] = '无法评估(停牌/亏损)'
        
        daily = get_daily_basic(pro, symbol)
        if daily:
            result['market'] = daily
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python fundamental_tushare.py <symbol> [mode]")
        sys.exit(1)
    
    symbol = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'full'
    
    result = analyze_fundamental(symbol, mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
