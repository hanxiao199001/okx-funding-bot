#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时交易信号监控
每分钟检查一次，给出交易建议
"""

import requests
import pandas as pd
from datetime import datetime
import time

# 策略参数
LONG_THRESHOLD = -0.003   # 做多阈值
SHORT_THRESHOLD = 0.003   # 做空阈值  
EXIT_THRESHOLD = 0.001    # 平仓阈值

# 手续费
MAKER_FEE = 0.02  # 0.02%
TAKER_FEE = 0.05  # 0.05%

# OKX API
API_BASE = "https://www.okx.com"

def get_current_data():
    """获取当前市场数据"""
    try:
        # 价格
        ticker_url = f"{API_BASE}/api/v5/market/ticker"
        ticker_params = {"instId": "BTC-USDT-SWAP"}
        ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)
        ticker_data = ticker_response.json()
        price = float(ticker_data['data'][0]['last'])
        
        # 资金费率
        funding_url = f"{API_BASE}/api/v5/public/funding-rate"
        funding_params = {"instId": "BTC-USDT-SWAP"}
        funding_response = requests.get(funding_url, params=funding_params, timeout=10)
        funding_data = funding_response.json()
        funding_rate = float(funding_data['data'][0]['fundingRate']) * 100
        
        # 持仓量
        oi_url = f"{API_BASE}/api/v5/public/open-interest"
        oi_params = {"instId": "BTC-USDT-SWAP"}
        oi_response = requests.get(oi_url, params=oi_params, timeout=10)
        oi_data = oi_response.json()
        open_interest_usd = float(oi_data['data'][0]['oiCcy'])
        
        return {
            'price': price,
            'funding_rate': funding_rate,
            'open_interest_usd': open_interest_usd,
            'timestamp': datetime.now()
        }
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None

def analyze_signal(data, position=None, entry_price=None):
    """分析交易信号"""
    
    funding_rate = data['funding_rate']
    price = data['price']
    
    # 无持仓
    if position is None:
        if funding_rate < LONG_THRESHOLD:
            return {
                'action': 'LONG',
                'reason': f'资金费率 {funding_rate:.4f}% < {LONG_THRESHOLD:.4f}%，做多可收费',
                'confidence': '高',
                'entry_price': price
            }
        elif funding_rate > SHORT_THRESHOLD:
            return {
                'action': 'SHORT',
                'reason': f'资金费率 {funding_rate:.4f}% > {SHORT_THRESHOLD:.4f}%，做空可收费',
                'confidence': '高',
                'entry_price': price
            }
        else:
            return {
                'action': 'WAIT',
                'reason': f'资金费率 {funding_rate:.4f}% 在中性区间，等待机会',
                'confidence': '中',
                'entry_price': None
            }
    
    # 持有多仓
    elif position == 'LONG':
        pnl = ((price - entry_price) / entry_price) * 100
        
        if abs(funding_rate) < EXIT_THRESHOLD:
            return {
                'action': 'CLOSE',
                'reason': f'资金费率回归中性 ({funding_rate:.4f}%)，获利平仓',
                'confidence': '高',
                'pnl': pnl
            }
        elif funding_rate > SHORT_THRESHOLD:
            return {
                'action': 'CLOSE',
                'reason': f'资金费率转为极度正值 ({funding_rate:.4f}%)，止损平仓',
                'confidence': '高',
                'pnl': pnl
            }
        elif pnl < -2.0:
            return {
                'action': 'CLOSE',
                'reason': f'亏损达到止损线 ({pnl:.2f}%)',
                'confidence': '高',
                'pnl': pnl
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'持有多仓，当前盈亏 {pnl:+.2f}%',
                'confidence': '中',
                'pnl': pnl
            }
    
    # 持有空仓
    elif position == 'SHORT':
        pnl = ((entry_price - price) / entry_price) * 100
        
        if abs(funding_rate) < EXIT_THRESHOLD:
            return {
                'action': 'CLOSE',
                'reason': f'资金费率回归中性 ({funding_rate:.4f}%)，获利平仓',
                'confidence': '高',
                'pnl': pnl
            }
        elif funding_rate < LONG_THRESHOLD:
            return {
                'action': 'CLOSE',
                'reason': f'资金费率转为极度负值 ({funding_rate:.4f}%)，止损平仓',
                'confidence': '高',
                'pnl': pnl
            }
        elif pnl > 1.5:
            return {
                'action': 'CLOSE',
                'reason': f'盈利达到目标 ({pnl:.2f}%)，获利了结',
                'confidence': '高',
                'pnl': pnl
            }
        elif pnl < -2.0:
            return {
                'action': 'CLOSE',
                'reason': f'亏损达到止损线 ({pnl:.2f}%)',
                'confidence': '高',
                'pnl': pnl
            }
        else:
            return {
                'action': 'HOLD',
                'reason': f'持有空仓，当前盈亏 {pnl:+.2f}%',
                'confidence': '中',
                'pnl': pnl
            }

def display_dashboard(data, signal):
    """显示监控面板"""
    
    print("\n" + "="*70)
    print(f"📊 实时交易监控 - {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    print(f"\n【市场数据】")
    print(f"  💰 BTC价格: ${data['price']:,.2f}")
    print(f"  📈 资金费率: {data['funding_rate']:.4f}%")
    print(f"  📊 持仓量: ${data['open_interest_usd']:,.0f}")
    
    print(f"\n【交易信号】")
    
    # 信号颜色
    if signal['action'] == 'LONG':
        emoji = "🟢"
    elif signal['action'] == 'SHORT':
        emoji = "🔴"
    elif signal['action'] == 'CLOSE':
        emoji = "⚪"
    else:
        emoji = "🟡"
    
    print(f"  {emoji} 操作建议: {signal['action']}")
    print(f"  💡 理由: {signal['reason']}")
    print(f"  🎯 信心度: {signal['confidence']}")
    
    if 'pnl' in signal:
        pnl_emoji = "📈" if signal['pnl'] > 0 else "📉"
        print(f"  {pnl_emoji} 当前盈亏: {signal['pnl']:+.2f}%")
    
    print(f"\n【参考信息】")
    print(f"  做多阈值: < {LONG_THRESHOLD:.4f}%")
    print(f"  做空阈值: > {SHORT_THRESHOLD:.4f}%")
    print(f"  平仓阈值: ± {EXIT_THRESHOLD:.4f}%")
    print(f"  手续费: Maker {MAKER_FEE}% / Taker {TAKER_FEE}%")
    
    print("="*70)

def monitor_once():
    """监控一次"""
    
    # 获取数据
    data = get_current_data()
    if data is None:
        return
    
    # 分析信号
    signal = analyze_signal(data)
    
    # 显示
    display_dashboard(data, signal)

def continuous_monitor(interval=60):
    """持续监控"""
    
    print("🚀 实时交易监控启动")
    print(f"⏰ 监控间隔: {interval}秒")
    print("⌨️  按 Ctrl+C 停止\n")
    
    try:
        while True:
            monitor_once()
            print(f"\n⏳ 等待 {interval} 秒后刷新...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        monitor_once()
    else:
        continuous_monitor(60)
