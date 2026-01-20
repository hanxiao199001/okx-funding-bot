#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化脚本
生成：资金费率图、价格图、策略信号图
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 设置中文字体（Mac）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (14, 8)

def load_data():
    """加载数据"""
    df = pd.read_csv('okx_btc_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def plot_funding_rate(df):
    """绘制资金费率走势图"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 资金费率曲线
    ax.plot(df['timestamp'], df['funding_rate'], 
            linewidth=2, color='#3498db', label='Funding Rate')
    
    # 填充区域
    ax.fill_between(df['timestamp'], df['funding_rate'], 0,
                     where=(df['funding_rate'] > 0),
                     alpha=0.3, color='red', label='Long Pay (>0)')
    
    ax.fill_between(df['timestamp'], df['funding_rate'], 0,
                     where=(df['funding_rate'] < 0),
                     alpha=0.3, color='green', label='Short Pay (<0)')
    
    # 阈值线
    ax.axhline(y=0.5, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Short Threshold (0.5%)')
    ax.axhline(y=-0.3, color='green', linestyle='--', linewidth=1, alpha=0.7, label='Long Threshold (-0.3%)')
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    # 格式化
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Funding Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('BTC Funding Rate Trend', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 时间格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('funding_rate_chart.png', dpi=300, bbox_inches='tight')
    print("✅ 资金费率图已保存: funding_rate_chart.png")
    plt.close()

def plot_price_and_funding(df):
    """绘制价格与资金费率双轴图"""
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # 价格（左轴）
    color1 = '#2c3e50'
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_ylabel('BTC Price (USD)', color=color1, fontsize=12, fontweight='bold')
    ax1.plot(df['timestamp'], df['price'], 
             color=color1, linewidth=2.5, label='BTC Price')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 资金费率（右轴）
    ax2 = ax1.twinx()
    color2 = '#e74c3c'
    ax2.set_ylabel('Funding Rate (%)', color=color2, fontsize=12, fontweight='bold')
    ax2.plot(df['timestamp'], df['funding_rate'], 
             color=color2, linewidth=2, linestyle='--', 
             marker='o', markersize=3, label='Funding Rate')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    # 标题
    plt.title('BTC Price vs Funding Rate', fontsize=16, fontweight='bold', pad=20)
    
    # 时间格式
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    # 图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('price_vs_funding.png', dpi=300, bbox_inches='tight')
    print("✅ 价格对比图已保存: price_vs_funding.png")
    plt.close()

def plot_strategy_signals(df):
    """绘制策略信号图"""
    
    # 生成信号
    df['signal'] = 'HOLD'
    df.loc[df['funding_rate'] > 0.5, 'signal'] = 'SHORT'
    df.loc[df['funding_rate'] < -0.3, 'signal'] = 'LONG'
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # 上图：价格 + 信号
    ax1.plot(df['timestamp'], df['price'], 
             color='#34495e', linewidth=2, label='BTC Price')
    
    # 标注信号点
    short_signals = df[df['signal'] == 'SHORT']
    long_signals = df[df['signal'] == 'LONG']
    
    if len(short_signals) > 0:
        ax1.scatter(short_signals['timestamp'], short_signals['price'],
                   color='red', s=100, marker='v', 
                   label='Short Signal', zorder=5, alpha=0.7)
    
    if len(long_signals) > 0:
        ax1.scatter(long_signals['timestamp'], long_signals['price'],
                   color='green', s=100, marker='^', 
                   label='Long Signal', zorder=5, alpha=0.7)
    
    ax1.set_ylabel('BTC Price (USD)', fontsize=12, fontweight='bold')
    ax1.set_title('Trading Strategy Signals', fontsize=16, fontweight='bold', pad=20)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 下图：资金费率
    colors = ['red' if x == 'SHORT' else 'green' if x == 'LONG' else 'gray' 
              for x in df['signal']]
    
    ax2.bar(df['timestamp'], df['funding_rate'], 
            color=colors, alpha=0.6, width=0.003)
    
    ax2.axhline(y=0.5, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax2.axhline(y=-0.3, color='green', linestyle='--', linewidth=1, alpha=0.7)
    ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Funding Rate (%)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 时间格式
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('strategy_signals.png', dpi=300, bbox_inches='tight')
    print("✅ 策略信号图已保存: strategy_signals.png")
    plt.close()

def plot_open_interest(df):
    """绘制持仓量变化"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.fill_between(df['timestamp'], df['open_interest_usd'], 
                     alpha=0.4, color='#9b59b6')
    ax.plot(df['timestamp'], df['open_interest_usd'], 
            color='#8e44ad', linewidth=2, label='Open Interest')
    
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Open Interest (USD)', fontsize=12, fontweight='bold')
    ax.set_title('BTC Open Interest Trend', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 时间格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('open_interest.png', dpi=300, bbox_inches='tight')
    print("✅ 持仓量图已保存: open_interest.png")
    plt.close()

def generate_summary_report(df):
    """生成数据摘要"""
    
    print("\n" + "="*70)
    print("📊 数据分析摘要")
    print("="*70)
    
    print(f"\n【数据范围】")
    print(f"起始时间: {df['timestamp'].min()}")
    print(f"结束时间: {df['timestamp'].max()}")
    print(f"数据量: {len(df)} 条")
    print(f"时间跨度: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600:.1f} 小时")
    
    print(f"\n【价格统计】")
    print(f"最高价: ${df['price'].max():,.2f}")
    print(f"最低价: ${df['price'].min():,.2f}")
    print(f"平均价: ${df['price'].mean():,.2f}")
    print(f"当前价: ${df['price'].iloc[-1]:,.2f}")
    print(f"区间波动: {(df['price'].max() - df['price'].min()) / df['price'].mean() * 100:.2f}%")
    
    print(f"\n【资金费率统计】")
    print(f"最高费率: {df['funding_rate'].max():.4f}%")
    print(f"最低费率: {df['funding_rate'].min():.4f}%")
    print(f"平均费率: {df['funding_rate'].mean():.4f}%")
    print(f"当前费率: {df['funding_rate'].iloc[-1]:.4f}%")
    
    # 信号统计
    short_count = len(df[df['funding_rate'] > 0.5])
    long_count = len(df[df['funding_rate'] < -0.3])
    
    print(f"\n【交易信号统计】")
    print(f"做空信号: {short_count} 次 ({short_count/len(df)*100:.1f}%)")
    print(f"做多信号: {long_count} 次 ({long_count/len(df)*100:.1f}%)")
    
    print("="*70 + "\n")

def main():
    """主函数"""
    
    print("\n" + "="*70)
    print("🎨 开始生成可视化图表...")
    print("="*70 + "\n")
    
    # 加载数据
    df = load_data()
    
    # 生成摘要
    generate_summary_report(df)
    
    # 生成图表
    print("正在生成图表...\n")
    
    plot_funding_rate(df)
    plot_price_and_funding(df)
    plot_strategy_signals(df)
    plot_open_interest(df)
    
    print("\n" + "="*70)
    print("✅ 所有图表生成完成！")
    print("="*70)
    print("\n生成的文件：")
    print("  📈 funding_rate_chart.png - 资金费率走势")
    print("  📊 price_vs_funding.png - 价格对比")
    print("  🎯 strategy_signals.png - 策略信号")
    print("  📉 open_interest.png - 持仓量趋势")
    print("\n使用 'open *.png' 查看所有图表")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
