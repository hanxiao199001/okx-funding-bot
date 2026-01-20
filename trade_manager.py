#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易管理器
功能：手动平仓、查看持仓、交易历史
"""

import json
import os
from datetime import datetime
import requests

STATE_FILE = 'paper_state.json'
HISTORY_FILE = 'trade_history.json'

def load_state():
    """加载当前状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_history():
    """加载交易历史"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'trades': [], 'total_pnl': 0, 'win_count': 0, 'loss_count': 0}

def save_history(history):
    """保存交易历史"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_current_price():
    """获取当前价格"""
    r = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP")
    return float(r.json()['data'][0]['last'])

def get_current_funding_rate():
    """获取当前资金费率"""
    r = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")
    return float(r.json()['data'][0]['fundingRate']) * 100

def show_position():
    """显示当前持仓"""
    state = load_state()
    
    if not state:
        print("\n❌ 未找到状态文件")
        return
    
    print("\n" + "="*60)
    print("📊 当前持仓状态")
    print("="*60)
    
    print(f"\n【账户信息】")
    print(f"余额: ${state['balance']:.2f}")
    
    if state['position']:
        current_price = get_current_price()
        entry_price = state['entry_price']
        
        # 计算盈亏
        if state['position'] == 'SHORT':
            pnl_ratio = ((entry_price - current_price) / entry_price) * 100 - 0.1
        else:
            pnl_ratio = ((current_price - entry_price) / entry_price) * 100 - 0.1
        
        position_size = state['balance'] * 0.3
        pnl_amount = position_size * (pnl_ratio / 100)
        
        print(f"\n【持仓详情】")
        print(f"方向: {state['position']}")
        print(f"开仓时间: {state['entry_time']}")
        print(f"开仓价格: ${entry_price:,.2f}")
        print(f"当前价格: ${current_price:,.2f}")
        print(f"仓位金额: ${position_size:.2f}")
        print(f"盈亏比例: {pnl_ratio:+.2f}%")
        print(f"盈亏金额: ${pnl_amount:+.2f}")
        
        # 风险提示
        if pnl_ratio < -1.5:
            print(f"\n⚠️  警告: 接近止损线!")
        elif pnl_ratio > 1.0:
            print(f"\n✅ 提示: 可考虑止盈")
        
    else:
        print(f"\n【持仓详情】")
        print(f"当前无持仓")
    
    print("="*60)

def close_position():
    """手动平仓"""
    state = load_state()
    
    if not state or not state['position']:
        print("\n❌ 当前无持仓，无法平仓")
        return
    
    # 显示当前持仓
    show_position()
    
    # 确认平仓
    print("\n⚠️  确认平仓操作")
    confirm = input("输入 'YES' 确认平仓，其他键取消: ")
    
    if confirm != 'YES':
        print("❌ 已取消")
        return
    
    # 获取平仓价格
    close_price = get_current_price()
    close_time = datetime.now().isoformat()
    entry_price = state['entry_price']
    
    # 计算盈亏
    if state['position'] == 'SHORT':
        pnl_ratio = ((entry_price - close_price) / entry_price) * 100 - 0.1
    else:
        pnl_ratio = ((close_price - entry_price) / entry_price) * 100 - 0.1
    
    position_size = state['balance'] * 0.3
    pnl_amount = position_size * (pnl_ratio / 100)
    
    # 更新余额
    new_balance = state['balance'] + pnl_amount
    
    # 保存交易记录
    history = load_history()
    
    trade_record = {
        'id': len(history['trades']) + 1,
        'type': state['position'],
        'entry_time': state['entry_time'],
        'entry_price': entry_price,
        'close_time': close_time,
        'close_price': close_price,
        'pnl_ratio': pnl_ratio,
        'pnl_amount': pnl_amount,
        'balance_before': state['balance'],
        'balance_after': new_balance
    }
    
    history['trades'].append(trade_record)
    history['total_pnl'] += pnl_amount
    
    if pnl_amount > 0:
        history['win_count'] += 1
    else:
        history['loss_count'] += 1
    
    save_history(history)
    
    # 更新状态
    state['position'] = None
    state['entry_price'] = 0
    state['entry_time'] = None
    state['balance'] = new_balance
    
    save_state(state)
    
    # 显示结果
    print("\n" + "="*60)
    print("✅ 平仓成功！")
    print("="*60)
    print(f"\n开仓价: ${entry_price:,.2f}")
    print(f"平仓价: ${close_price:,.2f}")
    print(f"盈亏: {pnl_ratio:+.2f}% (${pnl_amount:+.2f})")
    print(f"账户余额: ${state['balance']:.2f} → ${new_balance:.2f}")
    print("="*60 + "\n")

def show_history():
    """显示交易历史"""
    history = load_history()
    
    if not history['trades']:
        print("\n📋 暂无交易记录")
        return
    
    print("\n" + "="*60)
    print("📜 交易历史")
    print("="*60)
    
    for trade in history['trades']:
        print(f"\n【交易 #{trade['id']}】")
        print(f"类型: {trade['type']}")
        print(f"开仓: {trade['entry_time'][:19]} @ ${trade['entry_price']:,.2f}")
        print(f"平仓: {trade['close_time'][:19]} @ ${trade['close_price']:,.2f}")
        
        emoji = "📈" if trade['pnl_amount'] > 0 else "📉"
        print(f"盈亏: {emoji} {trade['pnl_ratio']:+.2f}% (${trade['pnl_amount']:+.2f})")
    
    print("\n" + "="*60)
    print("📊 总体统计")
    print("="*60)
    print(f"总交易次数: {len(history['trades'])} 笔")
    print(f"盈利交易: {history['win_count']} 笔")
    print(f"亏损交易: {history['loss_count']} 笔")
    
    if len(history['trades']) > 0:
        win_rate = history['win_count'] / len(history['trades']) * 100
        print(f"胜率: {win_rate:.1f}%")
    
    print(f"总盈亏: ${history['total_pnl']:+.2f}")
    print("="*60 + "\n")

def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("🎛️  交易管理器")
    print("="*60)
    print("\n1. 查看当前持仓")
    print("2. 手动平仓")
    print("3. 查看交易历史")
    print("4. 查看盈亏统计")
    print("5. 退出")
    print("\n" + "="*60)

def show_stats():
    """显示统计报告"""
    history = load_history()
    state = load_state()
    
    print("\n" + "="*60)
    print("📊 盈亏统计报告")
    print("="*60)
    
    if not state:
        print("\n❌ 未找到状态文件")
        return
    
    print(f"\n【账户概况】")
    print(f"初始资金: $50.00")
    print(f"当前余额: ${state['balance']:.2f}")
    total_return = ((state['balance'] - 50.0) / 50.0) * 100
    print(f"总收益率: {total_return:+.2f}%")
    
    if history['trades']:
        print(f"\n【交易统计】")
        print(f"完成交易: {len(history['trades'])} 笔")
        print(f"盈利笔数: {history['win_count']} 笔")
        print(f"亏损笔数: {history['loss_count']} 笔")
        
        win_rate = history['win_count'] / len(history['trades']) * 100
        print(f"胜率: {win_rate:.1f}%")
        
        avg_pnl = history['total_pnl'] / len(history['trades'])
        print(f"平均盈亏: ${avg_pnl:+.2f}")
        
        # 最大盈利/亏损
        pnls = [t['pnl_amount'] for t in history['trades']]
        print(f"最大盈利: ${max(pnls):+.2f}")
        print(f"最大亏损: ${min(pnls):+.2f}")
    
    # 如果有持仓，显示浮动盈亏
    if state['position']:
        current_price = get_current_price()
        entry_price = state['entry_price']
        
        if state['position'] == 'SHORT':
            pnl_ratio = ((entry_price - current_price) / entry_price) * 100 - 0.1
        else:
            pnl_ratio = ((current_price - entry_price) / entry_price) * 100 - 0.1
        
        position_size = state['balance'] * 0.3
        pnl_amount = position_size * (pnl_ratio / 100)
        
        print(f"\n【未实现盈亏】")
        print(f"持仓方向: {state['position']}")
        print(f"浮动盈亏: {pnl_ratio:+.2f}% (${pnl_amount:+.2f})")
        
        if pnl_amount > 0:
            potential_balance = state['balance'] + pnl_amount
            print(f"潜在余额: ${potential_balance:.2f}")
    
    print("="*60 + "\n")

def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == '1':
            show_position()
        elif choice == '2':
            close_position()
        elif choice == '3':
            show_history()
        elif choice == '4':
            show_stats()
        elif choice == '5':
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选择，请重试")
        
        input("\n按Enter继续...")

if __name__ == "__main__":
    main()
