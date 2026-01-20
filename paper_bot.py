#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纸面交易机器人 - 带状态保存"""

import requests
from datetime import datetime
import json
import os

STATE_FILE = 'paper_state.json'

# 策略参数
SHORT_THRESHOLD = 0.005
EXIT_THRESHOLD = 0.001
STOP_LOSS = -2.0
TAKE_PROFIT = 1.5

def load_state():
    """加载状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'balance': 50.0,
        'position': None,
        'entry_price': 0,
        'entry_time': None,
        'trades': []
    }

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_market():
    """获取市场数据"""
    r1 = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")
    price = float(r1.json()['data'][0]['last'])
    
    r2 = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")
    rate = float(r2.json()['data'][0]['fundingRate']) * 100
    
    return price, rate

def main():
    state = load_state()
    
    price, rate = get_market()
    
    print("\n" + "="*60)
    print(f"📊 纸面交易 - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    print(f"价格: ${price:,.2f}")
    print(f"资金费率: {rate:.4f}%")
    print(f"余额: ${state['balance']:.2f}")
    
    if state['position'] is None:
        # 无仓位 - 检查开仓
        if rate > SHORT_THRESHOLD:
            state['position'] = 'SHORT'
            state['entry_price'] = price
            state['entry_time'] = datetime.now().isoformat()
            
            print(f"\n🔴 开空仓")
            print(f"开仓价: ${price:,.2f}")
            
            state['trades'].append({
                'action': 'OPEN_SHORT',
                'price': price,
                'rate': rate,
                'time': state['entry_time']
            })
            
            save_state(state)
        else:
            print(f"\n🟡 等待信号 (费率需 > {SHORT_THRESHOLD:.4f}%)")
    
    else:
        # 有仓位 - 计算盈亏
        pnl = ((state['entry_price'] - price) / state['entry_price']) * 100 - 0.1
        pnl_amount = state['balance'] * 0.3 * (pnl / 100)
        
        print(f"\n【持仓信息】")
        print(f"方向: {state['position']}")
        print(f"开仓价: ${state['entry_price']:,.2f}")
        print(f"当前价: ${price:,.2f}")
        print(f"盈亏: {pnl:+.2f}% (${pnl_amount:+.2f})")
        
        # 检查平仓
        should_close = False
        close_reason = ""
        
        if abs(rate) < EXIT_THRESHOLD:
            should_close = True
            close_reason = "费率回归中性"
        elif pnl > TAKE_PROFIT:
            should_close = True
            close_reason = "达到止盈"
        elif pnl < STOP_LOSS:
            should_close = True
            close_reason = "触发止损"
        
        if should_close:
            print(f"\n⚪ 建议平仓: {close_reason}")
            print(f"输入 'close' 确认平仓")
        else:
            print(f"\n✅ 继续持有")
    
    print("="*60)

if __name__ == "__main__":
    import sys
    import time
    
    if len(sys.argv) > 1 and sys.argv[1] == 'loop':
        print("🚀 启动持续监控（每5分钟）")
        print("按 Ctrl+C 停止\n")
        try:
            while True:
                main()
                print("\n⏳ 等待5分钟...\n")
                time.sleep(300)
        except KeyboardInterrupt:
            print("\n\n⏹️  已停止")
    else:
        main()
