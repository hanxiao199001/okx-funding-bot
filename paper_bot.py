#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纸面交易机器人 - 简化版"""

import requests
from datetime import datetime

# 初始资金
balance = 50.0
position = None  # None, 'LONG', 'SHORT'
entry_price = 0

# 策略参数
SHORT_THRESHOLD = 0.005  # 0.5%做空

def get_market():
    """获取市场数据"""
    # 价格
    r1 = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")
    price = float(r1.json()['data'][0]['last'])
    
    # 资金费率
    r2 = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")
    rate = float(r2.json()['data'][0]['fundingRate']) * 100
    
    return price, rate

def main():
    global position, entry_price, balance
    
    price, rate = get_market()
    
    print("\n" + "="*60)
    print(f"📊 纸面交易 - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    print(f"价格: ${price:,.2f}")
    print(f"资金费率: {rate:.4f}%")
    print(f"余额: ${balance:.2f}")
    
    if position is None:
        # 无仓位 - 检查开仓
        if rate > SHORT_THRESHOLD:
            position = 'SHORT'
            entry_price = price
            print(f"\n🔴 模拟开空")
            print(f"开仓价: ${entry_price:,.2f}")
        else:
            print(f"\n🟡 等待信号 (费率需要 > {SHORT_THRESHOLD:.4f}%)")
    
    else:
        # 有仓位 - 显示盈亏
        pnl = ((entry_price - price) / entry_price) * 100 - 0.1  # 减手续费
        print(f"\n【当前持仓】")
        print(f"方向: {position}")
        print(f"开仓价: ${entry_price:,.2f}")
        print(f"盈亏: {pnl:+.2f}%")
        
        # 检查平仓条件
        if abs(rate) < 0.001:
            print(f"\n⚪ 建议平仓 (费率回归)")
        elif pnl > 1.5:
            print(f"\n⚪ 建议平仓 (止盈)")
        elif pnl < -2.0:
            print(f"\n⚪ 建议平仓 (止损)")
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
