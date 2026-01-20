#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略参数优化 - 网格搜索最优参数
"""

import pandas as pd
import numpy as np
from funding_strategy import FundingRateStrategy
import itertools

def test_parameters(data_file='okx_btc_data.csv', 
                   long_threshold=-0.003,
                   short_threshold=0.005,
                   exit_threshold=0.001):
    """测试特定参数组合"""
    
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    strategy = FundingRateStrategy(
        long_threshold=long_threshold,
        short_threshold=short_threshold,
        exit_threshold=exit_threshold
    )
    
    trades = []
    total_pnl = 0
    
    for idx, row in df.iterrows():
        signal = strategy.generate_signal(
            row['funding_rate'],
            row['price'],
            row['timestamp']
        )
        
        if signal in ['LONG', 'SHORT']:
            trades.append({
                'type': signal,
                'entry_price': row['price'],
                'entry_time': row['timestamp'],
                'entry_funding': row['funding_rate']
            })
        
        elif signal == 'CLOSE' and len(trades) > 0:
            last_trade = trades[-1]
            
            if last_trade['type'] == 'LONG':
                pnl = ((row['price'] - last_trade['entry_price']) / last_trade['entry_price']) * 100
            else:  # SHORT
                pnl = ((last_trade['entry_price'] - row['price']) / last_trade['entry_price']) * 100
            
            # 减去手续费 (开仓0.05% + 平仓0.05%)
            pnl -= 0.1
            
            total_pnl += pnl
            
            trades[-1]['exit_price'] = row['price']
            trades[-1]['exit_time'] = row['timestamp']
            trades[-1]['pnl'] = pnl
    
    # 统计
    completed_trades = [t for t in trades if 'pnl' in t]
    win_trades = [t for t in completed_trades if t['pnl'] > 0]
    
    return {
        'total_trades': len(completed_trades),
        'win_rate': len(win_trades) / len(completed_trades) * 100 if completed_trades else 0,
        'total_pnl': total_pnl,
        'avg_pnl': total_pnl / len(completed_trades) if completed_trades else 0,
        'max_pnl': max([t['pnl'] for t in completed_trades]) if completed_trades else 0,
        'min_pnl': min([t['pnl'] for t in completed_trades]) if completed_trades else 0
    }


def grid_search():
    """网格搜索最优参数"""
    
    print("="*70)
    print("🔍 策略参数优化 - 网格搜索")
    print("="*70)
    
    # 参数范围
    long_thresholds = [-0.005, -0.003, -0.001]  # 做多阈值
    short_thresholds = [0.003, 0.005, 0.007]     # 做空阈值
    exit_thresholds = [0.0005, 0.001, 0.002]     # 平仓阈值
    
    results = []
    
    print(f"\n测试参数组合数: {len(long_thresholds) * len(short_thresholds) * len(exit_thresholds)}")
    print("正在测试...\n")
    
    for lt, st, et in itertools.product(long_thresholds, short_thresholds, exit_thresholds):
        result = test_parameters(
            long_threshold=lt,
            short_threshold=st,
            exit_threshold=et
        )
        
        result['long_threshold'] = lt
        result['short_threshold'] = st
        result['exit_threshold'] = et
        
        results.append(result)
    
    # 转为DataFrame
    df = pd.DataFrame(results)
    
    # 按总盈亏排序
    df = df.sort_values('total_pnl', ascending=False)
    
    print("="*70)
    print("📊 优化结果 (按总盈亏排序，前10名)")
    print("="*70)
    print(f"\n{'排名':<4} {'做空阈值':<8} {'平仓阈值':<8} {'交易次数':<8} {'胜率':<8} {'总盈亏':<10} {'平均盈亏':<10}")
    print("-"*70)
    
    for idx, row in df.head(10).iterrows():
        print(f"{df.index.get_loc(idx)+1:<4} "
              f"{row['short_threshold']:<8.4f} "
              f"{row['exit_threshold']:<8.4f} "
              f"{int(row['total_trades']):<8} "
              f"{row['win_rate']:<8.1f} "
              f"{row['total_pnl']:<10.2f} "
              f"{row['avg_pnl']:<10.2f}")
    
    # 最优参数
    best = df.iloc[0]
    
    print("\n" + "="*70)
    print("🏆 最优参数组合")
    print("="*70)
    print(f"做多阈值: {best['long_threshold']:.4f}%")
    print(f"做空阈值: {best['short_threshold']:.4f}%")
    print(f"平仓阈值: {best['exit_threshold']:.4f}%")
    print(f"\n性能指标:")
    print(f"  总交易次数: {int(best['total_trades'])} 次")
    print(f"  胜率: {best['win_rate']:.1f}%")
    print(f"  总盈亏: {best['total_pnl']:.2f}%")
    print(f"  平均盈亏: {best['avg_pnl']:.2f}%")
    print(f"  最大单笔: {best['max_pnl']:.2f}%")
    print(f"  最小单笔: {best['min_pnl']:.2f}%")
    print("="*70)
    
    # 保存结果
    df.to_csv('optimization_results.csv', index=False)
    print(f"\n✅ 完整结果已保存到: optimization_results.csv")
    
    return df


def quick_comparison():
    """快速对比几个常用参数"""
    
    print("="*70)
    print("⚡ 快速参数对比")
    print("="*70)
    
    configs = [
        {'name': '保守型', 'long': -0.005, 'short': 0.005, 'exit': 0.001},
        {'name': '平衡型', 'long': -0.003, 'short': 0.003, 'exit': 0.001},
        {'name': '激进型', 'long': -0.001, 'short': 0.002, 'exit': 0.0005},
    ]
    
    print(f"\n{'策略':<8} {'交易次数':<8} {'胜率':<8} {'总盈亏':<10} {'平均盈亏':<10}")
    print("-"*70)
    
    for config in configs:
        result = test_parameters(
            long_threshold=config['long'],
            short_threshold=config['short'],
            exit_threshold=config['exit']
        )
        
        print(f"{config['name']:<8} "
              f"{int(result['total_trades']):<8} "
              f"{result['win_rate']:<8.1f} "
              f"{result['total_pnl']:<10.2f} "
              f"{result['avg_pnl']:<10.2f}")
    
    print("="*70)


if __name__ == "__main__":
    # 先快速对比
    quick_comparison()
    
    print("\n")
    
    # 详细网格搜索
    grid_search()
