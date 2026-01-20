#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盈亏追踪可视化
实时显示持仓盈亏曲线
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import json
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_state():
    """加载交易状态"""
    if os.path.exists('paper_state.json'):
        with open('paper_state.json', 'r') as f:
            return json.load(f)
    return None

def calculate_pnl_series():
    """计算盈亏序列"""
    state = load_state()
    
    if not state or not state['position']:
        print("❌ 当前无持仓，无法生成盈亏曲线")
        return None
    
    # 加载历史数据
    df = pd.read_csv('okx_btc_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 找到开仓时间之后的数据
    entry_time = pd.to_datetime(state['entry_time'])
    df_after_entry = df[df['timestamp'] >= entry_time].copy()
    
    if len(df_after_entry) == 0:
        print("❌ 开仓后没有数据")
        return None
    
    entry_price = state['entry_price']
    position_type = state['position']
    position_size = state['balance'] * 0.3
    
    # 计算每个时间点的盈亏
    if position_type == 'SHORT':
        df_after_entry['pnl_ratio'] = ((entry_price - df_after_entry['price']) / entry_price) * 100 - 0.1
    else:  # LONG
        df_after_entry['pnl_ratio'] = ((df_after_entry['price'] - entry_price) / entry_price) * 100 - 0.1
    
    df_after_entry['pnl_amount'] = position_size * (df_after_entry['pnl_ratio'] / 100)
    df_after_entry['balance'] = state['balance'] + df_after_entry['pnl_amount']
    
    return df_after_entry, state

def plot_pnl_curve():
    """绘制盈亏曲线"""
    
    result = calculate_pnl_series()
    if not result:
        return
    
    df, state = result
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    
    # 图1: 价格走势 + 开仓点
    ax1.plot(df['timestamp'], df['price'], 
             linewidth=2, color='#2c3e50', label='BTC Price')
    
    # 标注开仓点
    entry_time = pd.to_datetime(state['entry_time'])
    entry_price = state['entry_price']
    
    if state['position'] == 'SHORT':
        ax1.scatter([entry_time], [entry_price], 
                   color='red', s=200, marker='v', 
                   label='Short Entry', zorder=5, edgecolors='black', linewidths=2)
    else:
        ax1.scatter([entry_time], [entry_price], 
                   color='green', s=200, marker='^', 
                   label='Long Entry', zorder=5, edgecolors='black', linewidths=2)
    
    # 开仓价格线
    ax1.axhline(y=entry_price, color='gray', linestyle='--', 
                linewidth=1, alpha=0.5, label=f'Entry Price: ${entry_price:,.2f}')
    
    ax1.set_ylabel('Price (USD)', fontsize=12, fontweight='bold')
    ax1.set_title(f'{state["position"]} Position - Price Movement', 
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 图2: 盈亏比例曲线
    colors = ['green' if x > 0 else 'red' for x in df['pnl_ratio']]
    ax2.fill_between(df['timestamp'], df['pnl_ratio'], 0, 
                     alpha=0.3, color=colors[0])
    ax2.plot(df['timestamp'], df['pnl_ratio'], 
             linewidth=2.5, color='#3498db', label='PnL %')
    
    # 止盈止损线
    ax2.axhline(y=1.5, color='green', linestyle='--', 
                linewidth=1.5, alpha=0.7, label='Take Profit (+1.5%)')
    ax2.axhline(y=-2.0, color='red', linestyle='--', 
                linewidth=1.5, alpha=0.7, label='Stop Loss (-2%)')
    ax2.axhline(y=0, color='gray', linestyle='-', 
                linewidth=1, alpha=0.5)
    
    ax2.set_ylabel('PnL (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Profit & Loss Ratio', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 图3: 账户余额
    ax3.plot(df['timestamp'], df['balance'], 
             linewidth=3, color='#27ae60', label='Account Balance')
    ax3.axhline(y=state['balance'], color='gray', linestyle='--', 
                linewidth=1, alpha=0.5, label=f'Initial: ${state["balance"]:.2f}')
    
    # 填充盈利/亏损区域
    ax3.fill_between(df['timestamp'], df['balance'], state['balance'],
                     where=(df['balance'] > state['balance']),
                     alpha=0.3, color='green', label='Profit')
    ax3.fill_between(df['timestamp'], df['balance'], state['balance'],
                     where=(df['balance'] < state['balance']),
                     alpha=0.3, color='red', label='Loss')
    
    ax3.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Balance (USD)', fontsize=12, fontweight='bold')
    ax3.set_title('Account Balance Evolution', fontsize=14, fontweight='bold')
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    # 格式化时间轴
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('pnl_tracking.png', dpi=300, bbox_inches='tight')
    print("✅ 盈亏曲线已保存: pnl_tracking.png")
    plt.close()
    
    # 打印统计
    print("\n" + "="*60)
    print("📊 持仓盈亏统计")
    print("="*60)
    print(f"\n开仓时间: {state['entry_time']}")
    print(f"持仓时长: {(df['timestamp'].max() - entry_time).total_seconds() / 3600:.1f} 小时")
    print(f"开仓价格: ${entry_price:,.2f}")
    print(f"当前价格: ${df['price'].iloc[-1]:,.2f}")
    print(f"最高盈亏: {df['pnl_ratio'].max():+.2f}%")
    print(f"最低盈亏: {df['pnl_ratio'].min():+.2f}%")
    print(f"当前盈亏: {df['pnl_ratio'].iloc[-1]:+.2f}%")
    print(f"当前余额: ${df['balance'].iloc[-1]:.2f}")
    print("="*60 + "\n")

def main():
    print("\n🎨 生成盈亏追踪图表...")
    plot_pnl_curve()
    print("\n使用 'open pnl_tracking.png' 查看图表")

if __name__ == "__main__":
    main()
