#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略参数对比可视化
对比0.3%、0.5%、0.7%三个阈值的表现
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    df = pd.read_csv('okx_btc_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')

def simulate_strategy(df, threshold):
    """模拟策略表现"""
    signals = []
    in_position = False
    entry_price = 0
    entry_time = None
    
    for idx, row in df.iterrows():
        if not in_position and row['funding_rate'] > threshold:
            # 开空仓
            in_position = True
            entry_price = row['price']
            entry_time = row['timestamp']
            signals.append({
                'timestamp': row['timestamp'],
                'action': 'OPEN_SHORT',
                'price': row['price'],
                'rate': row['funding_rate']
            })
            
        elif in_position and abs(row['funding_rate']) < 0.001:
            # 平仓
            pnl = ((entry_price - row['price']) / entry_price) * 100 - 0.1
            signals.append({
                'timestamp': row['timestamp'],
                'action': 'CLOSE',
                'price': row['price'],
                'rate': row['funding_rate'],
                'pnl': pnl,
                'duration': (row['timestamp'] - entry_time).total_seconds() / 3600
            })
            in_position = False
    
    return signals

def plot_comparison():
    """生成对比图表"""
    df = load_data()
    
    # 三个策略
    strategies = [
        {'name': '激进(0.3%)', 'threshold': 0.003, 'color': 'red'},
        {'name': '当前(0.5%)', 'threshold': 0.005, 'color': 'orange'},
        {'name': '保守(0.7%)', 'threshold': 0.007, 'color': 'green'}
    ]
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 图1: 资金费率 + 不同阈值线
    ax1.plot(df['timestamp'], df['funding_rate'], 
             linewidth=1.5, color='#3498db', alpha=0.7, label='实际费率')
    
    for strategy in strategies:
        ax1.axhline(y=strategy['threshold'], 
                   color=strategy['color'], linestyle='--', 
                   linewidth=2, alpha=0.7, label=f"{strategy['name']}阈值")
    
    ax1.axhline(y=0.001, color='gray', linestyle=':', 
               linewidth=1, alpha=0.5, label='平仓阈值(0.1%)')
    
    ax1.set_ylabel('资金费率 (%)', fontsize=12, fontweight='bold')
    ax1.set_title('资金费率走势 vs 策略阈值', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # 图2: 信号频率对比
    signal_counts = []
    for strategy in strategies:
        signals = simulate_strategy(df, strategy['threshold'])
        open_signals = [s for s in signals if s['action'] == 'OPEN_SHORT']
        signal_counts.append(len(open_signals))
    
    colors = [s['color'] for s in strategies]
    names = [s['name'] for s in strategies]
    
    bars = ax2.bar(names, signal_counts, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('信号次数', fontsize=12, fontweight='bold')
    ax2.set_title('开仓信号频率对比', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 在柱子上显示数值
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')
    
    # 图3: 理论收益对比
    total_pnls = []
    for strategy in strategies:
        signals = simulate_strategy(df, strategy['threshold'])
        close_signals = [s for s in signals if s['action'] == 'CLOSE']
        total_pnl = sum([s['pnl'] for s in close_signals])
        total_pnls.append(total_pnl)
    
    bars = ax3.bar(names, total_pnls, color=colors, alpha=0.7, edgecolor='black')
    ax3.set_ylabel('累计收益率 (%)', fontsize=12, fontweight='bold')
    ax3.set_title('理论收益对比', fontsize=14, fontweight='bold')
    ax3.axhline(y=0, color='black', linewidth=1)
    ax3.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontweight='bold')
    
    # 图4: 平均持仓时长对比
    avg_durations = []
    for strategy in strategies:
        signals = simulate_strategy(df, strategy['threshold'])
        close_signals = [s for s in signals if s['action'] == 'CLOSE']
        if close_signals:
            avg_duration = np.mean([s['duration'] for s in close_signals])
        else:
            avg_duration = 0
        avg_durations.append(avg_duration)
    
    bars = ax4.bar(names, avg_durations, color=colors, alpha=0.7, edgecolor='black')
    ax4.set_ylabel('平均持仓时长 (小时)', fontsize=12, fontweight='bold')
    ax4.set_title('持仓时长对比', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}h',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('strategy_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ 策略对比图已保存: strategy_comparison.png")
    plt.close()
    
    # 打印详细统计
    print("\n" + "="*70)
    print("📊 策略对比统计")
    print("="*70)
    print(f"\n{'策略':<15} {'信号次数':<10} {'完成交易':<10} {'累计收益':<12} {'平均持仓':<10}")
    print("-"*70)
    
    for i, strategy in enumerate(strategies):
        signals = simulate_strategy(df, strategy['threshold'])
        open_signals = [s for s in signals if s['action'] == 'OPEN_SHORT']
        close_signals = [s for s in signals if s['action'] == 'CLOSE']
        
        print(f"{strategy['name']:<15} {len(open_signals):<10} {len(close_signals):<10} "
              f"{total_pnls[i]:<12.2f}% {avg_durations[i]:<10.1f}h")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    plot_comparison()
