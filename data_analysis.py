#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度数据分析
分析34小时数据，找出最佳策略参数
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_and_clean_data():
    """加载并清理数据"""
    df = pd.read_csv('okx_btc_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 按时间排序
    df = df.sort_values('timestamp')
    
    # 删除重复数据
    df = df.drop_duplicates(subset=['timestamp'])
    
    return df

def analyze_funding_rate_patterns(df):
    """分析资金费率模式"""
    
    print("\n" + "="*70)
    print("📊 资金费率深度分析")
    print("="*70)
    
    # 基础统计
    print(f"\n【基础统计】")
    print(f"数据量: {len(df)} 条")
    print(f"时间跨度: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600:.1f} 小时")
    print(f"平均费率: {df['funding_rate'].mean():.4f}%")
    print(f"中位数费率: {df['funding_rate'].median():.4f}%")
    print(f"标准差: {df['funding_rate'].std():.4f}%")
    
    # 费率区间分布
    print(f"\n【费率区间分布】")
    
    bins = [-float('inf'), -0.005, -0.003, 0, 0.003, 0.005, 0.007, float('inf')]
    labels = ['极负(<-0.5%)', '负(-0.5%~-0.3%)', '弱负(-0.3%~0)', 
              '弱正(0~0.3%)', '中正(0.3%~0.5%)', '高正(0.5%~0.7%)', '极高(>0.7%)']
    
    df['rate_category'] = pd.cut(df['funding_rate'], bins=bins, labels=labels)
    
    for category in labels:
        count = len(df[df['rate_category'] == category])
        pct = count / len(df) * 100
        print(f"  {category}: {count} 次 ({pct:.1f}%)")
    
    # 持续时间分析
    print(f"\n【高费率持续时间分析】")
    
    # 找出连续高费率区间（>0.5%）
    df['high_rate'] = df['funding_rate'] > 0.005
    df['rate_group'] = (df['high_rate'] != df['high_rate'].shift()).cumsum()
    
    high_rate_periods = df[df['high_rate']].groupby('rate_group').agg({
        'timestamp': ['min', 'max', 'count'],
        'funding_rate': 'mean'
    })
    
    if len(high_rate_periods) > 0:
        print(f"\n找到 {len(high_rate_periods)} 个高费率区间（>0.5%）:")
        for idx, period in high_rate_periods.iterrows():
            duration = (period[('timestamp', 'max')] - period[('timestamp', 'min')]).total_seconds() / 3600
            count = period[('timestamp', 'count')]
            avg_rate = period[('funding_rate', 'mean')]
            print(f"  区间{idx}: {duration:.1f}小时 ({count}个点) | 平均费率: {avg_rate:.4f}%")
    
    # 费率变化速度
    df['rate_change'] = df['funding_rate'].diff()
    
    print(f"\n【费率变化速度】")
    print(f"最大上涨速度: {df['rate_change'].max():.4f}% /5分钟")
    print(f"最大下跌速度: {df['rate_change'].min():.4f}% /5分钟")
    print(f"平均变化幅度: {df['rate_change'].abs().mean():.4f}% /5分钟")
    
    return df

def simulate_strategy_performance(df):
    """回测不同策略参数"""
    
    print("\n" + "="*70)
    print("🎯 策略参数优化分析")
    print("="*70)
    
    # 测试不同的阈值组合
    threshold_combinations = [
        {'name': '保守型', 'short': 0.007, 'exit': 0.001},
        {'name': '当前策略', 'short': 0.005, 'exit': 0.001},
        {'name': '激进型', 'short': 0.003, 'exit': 0.001},
        {'name': '超激进', 'short': 0.002, 'exit': 0.0005},
    ]
    
    print(f"\n{'策略':<12} {'信号次数':<8} {'平均持仓时长':<12} {'理论收益率':<12}")
    print("-"*70)
    
    for combo in threshold_combinations:
        signals = df[df['funding_rate'] > combo['short']]
        
        if len(signals) == 0:
            print(f"{combo['name']:<12} {'0':<8} {'-':<12} {'-':<12}")
            continue
        
        # 简单模拟：每次信号开仓，费率回落到exit阈值平仓
        total_pnl = 0
        trades = 0
        total_duration = 0
        
        in_position = False
        entry_price = 0
        entry_idx = 0
        
        for idx, row in df.iterrows():
            if not in_position and row['funding_rate'] > combo['short']:
                # 开仓
                in_position = True
                entry_price = row['price']
                entry_idx = idx
                
            elif in_position and abs(row['funding_rate']) < combo['exit']:
                # 平仓
                pnl = ((entry_price - row['price']) / entry_price) * 100 - 0.1
                total_pnl += pnl
                trades += 1
                
                duration = (row['timestamp'] - df.loc[entry_idx, 'timestamp']).total_seconds() / 3600
                total_duration += duration
                
                in_position = False
        
        avg_duration = total_duration / trades if trades > 0 else 0
        
        print(f"{combo['name']:<12} {len(signals):<8} {avg_duration:<12.1f} {total_pnl:<12.2f}%")
    
def find_best_entry_timing(df):
    """找出最佳开仓时机特征"""
    
    print("\n" + "="*70)
    print("⏰ 最佳开仓时机分析")
    print("="*70)
    
    # 添加时间特征
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # 按小时统计平均费率
    hourly_avg = df.groupby('hour')['funding_rate'].agg(['mean', 'max', 'count'])
    
    print(f"\n【每小时平均费率】")
    print(f"{'小时':<6} {'平均费率':<10} {'最高费率':<10} {'数据点数':<8}")
    print("-"*70)
    
    for hour in range(24):
        if hour in hourly_avg.index:
            avg = hourly_avg.loc[hour, 'mean']
            max_rate = hourly_avg.loc[hour, 'max']
            count = hourly_avg.loc[hour, 'count']
            print(f"{hour:02d}:00  {avg:>9.4f}%  {max_rate:>9.4f}%  {int(count):>7}")
    
    # 找出最佳时间段
    best_hours = hourly_avg.nlargest(3, 'mean')
    
    print(f"\n【最佳交易时段】（平均费率最高）")
    for hour, data in best_hours.iterrows():
        print(f"  {hour:02d}:00 - 平均费率: {data['mean']:.4f}%")
    
    # 价格波动与费率关系
    df['price_change'] = df['price'].pct_change() * 100
    
    correlation = df['price_change'].corr(df['funding_rate'])
    
    print(f"\n【价格与费率关系】")
    print(f"相关系数: {correlation:.4f}")
    
    if abs(correlation) < 0.3:
        print(f"结论: 价格变化与费率相关性较弱")
    elif correlation < 0:
        print(f"结论: 价格下跌时费率倾向上升（做空机会）")
    else:
        print(f"结论: 价格上涨时费率倾向上升")

def generate_recommendation(df):
    """生成策略建议"""
    
    print("\n" + "="*70)
    print("💡 策略优化建议")
    print("="*70)
    
    avg_rate = df['funding_rate'].mean()
    high_rate_pct = len(df[df['funding_rate'] > 0.005]) / len(df) * 100
    
    print(f"\n【当前市场特征】")
    print(f"  平均费率: {avg_rate:.4f}%")
    print(f"  高费率时间占比: {high_rate_pct:.1f}%")
    
    print(f"\n【策略建议】")
    
    if avg_rate > 0.005:
        print(f"  ✅ 市场偏多头，适合做空策略")
        print(f"  ✅ 建议保持当前参数（做空阈值0.5%）")
    elif avg_rate > 0.003:
        print(f"  ⚠️  市场中性偏多，可考虑降低做空阈值到0.3%")
    else:
        print(f"  ⚠️  市场中性，考虑同时启用做多和做空策略")
    
    if high_rate_pct > 50:
        print(f"  ✅ 交易机会充足（{high_rate_pct:.1f}%时间有信号）")
    else:
        print(f"  ⚠️  交易机会较少，考虑降低阈值或扩大交易范围")

def main():
    print("\n" + "="*70)
    print("🔍 开始深度数据分析...")
    print("="*70)
    
    # 加载数据
    df = load_and_clean_data()
    
    # 各项分析
    df = analyze_funding_rate_patterns(df)
    simulate_strategy_performance(df)
    find_best_entry_timing(df)
    generate_recommendation(df)
    
    print("\n" + "="*70)
    print("✅ 分析完成！")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
