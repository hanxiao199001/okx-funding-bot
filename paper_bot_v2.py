#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纸面交易机器人 - 优化版（带错误重试）"""

import requests
from datetime import datetime
import json
import os
import time

STATE_FILE = 'paper_state.json'

# 策略参数
SHORT_THRESHOLD = 0.003
EXIT_THRESHOLD = 0.001
STOP_LOSS = -2.0
TAKE_PROFIT = 1.5

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5

def fetch_with_retry(url, retries=MAX_RETRIES):
    """带重试的HTTP请求"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️  网络错误 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ 获取数据失败，跳过本次检查")
                return None
    return None

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
    # 价格
    r1_data = fetch_with_retry("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")
    if not r1_data:
        return None, None
    
    price = float(r1_data['data'][0]['last'])
    
    # 资金费率
    r2_data = fetch_with_retry("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")
    if not r2_data:
        return None, None
    
    rate = float(r2_data['data'][0]['fundingRate']) * 100
    
    return price, rate

def main():
    state = load_state()
    
    result = get_market()
    if result == (None, None):
        print("⚠️  无法获取市场数据，等待下次尝试...")
        return
    
    price, rate = result
    
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
            print(f"\n⚪ 平仓: {close_reason}")
            
            # 更新余额
            state['balance'] += pnl_amount
            
            state['trades'].append({
                'action': 'CLOSE',
                'price': price,
                'rate': rate,
                'pnl': pnl,
                'time': datetime.now().isoformat()
            })
            
            state['position'] = None
            state['entry_price'] = 0
            state['entry_time'] = None
            
            save_state(state)
            print(f"新余额: ${state['balance']:.2f}")
        else:
            print(f"\n✅ 继续持有")
    
    print("="*60)

if __name__ == "__main__":
    import sys
    import time
    
    if len(sys.argv) > 1 and sys.argv[1] == 'loop':
        print("🚀 启动持续监控（每5分钟，优化版）")
        print("✨ 新功能：自动错误重试、网络故障恢复")
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
