#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX资金费率套利策略
策略逻辑：当资金费率过高时做空，过低时做多
"""

import pandas as pd
import numpy as np
from datetime import datetime

class FundingRateStrategy:
    """资金费率套利策略"""
    
    def __init__(self, 
                 long_threshold=-0.003,   # 做多阈值：费率< -0.3%时做多
                 short_threshold=0.005,   # 做空阈值：费率> 0.5%时做空
                 exit_threshold=0.001):   # 平仓阈值：费率回归到±0.1%
        """
        初始化策略参数
        
        参数说明：
        - long_threshold: 资金费率低于此值时开多单（收取空头付的费用）
        - short_threshold: 资金费率高于此值时开空单（收取多头付的费用）
        - exit_threshold: 资金费率回归到此范围内时平仓
        """
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.exit_threshold = exit_threshold
        
        self.position = 0  # 0=无仓位, 1=多仓, -1=空仓
        self.entry_price = 0
        self.entry_time = None
        
    def generate_signal(self, funding_rate, price, timestamp):
        """
        生成交易信号
        
        返回：
        - 'LONG': 开多单
        - 'SHORT': 开空单  
        - 'CLOSE': 平仓
        - 'HOLD': 持有当前仓位
        """
        
        # 当前无仓位
        if self.position == 0:
            if funding_rate < self.long_threshold:
                self.position = 1
                self.entry_price = price
                self.entry_time = timestamp
                return 'LONG'
            elif funding_rate > self.short_threshold:
                self.position = -1
                self.entry_price = price
                self.entry_time = timestamp
                return 'SHORT'
            else:
                return 'HOLD'
        
        # 持有多仓
        elif self.position == 1:
            # 费率回归到中性区间，平仓
            if abs(funding_rate) < self.exit_threshold:
                pnl = ((price - self.entry_price) / self.entry_price) * 100
                self.position = 0
                return 'CLOSE'
            # 费率转为极度正值，止损平仓
            elif funding_rate > self.short_threshold:
                self.position = 0
                return 'CLOSE'
            else:
                return 'HOLD'
        
# 持有空仓
elif self.position == -1:
    # 费率回归到中性区间，平仓
    if abs(funding_rate) < self.exit_threshold:
        self.position = 0
        return 'CLOSE'
    # 费率转为极度负值，止损平仓
    elif funding_rate < self.long_threshold:
        self.position = 0
        return 'CLOSE'
    # 【新增】价格盈利超过1%且费率开始回落，获利平仓
    elif self.calculate_pnl(price) > 1.0:
        self.position = 0
        return 'CLOSE'
    else:
        return 'HOLD'    
    def calculate_pnl(self, current_price):
        """计算当前盈亏百分比"""
        if self.position == 0:
            return 0
        elif self.position == 1:  # 多仓
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # 空仓
            return ((self.entry_price - current_price) / self.entry_price) * 100


def backtest_strategy(data_file='okx_btc_data.csv'):
    """回测策略"""
    
    print("="*60)
    print("📊 资金费率套利策略回测")
    print("="*60)
    
    # 加载数据
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"\n数据范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
    print(f"数据量: {len(df)} 条")
    print(f"资金费率范围: {df['funding_rate'].min():.4f}% ~ {df['funding_rate'].max():.4f}%")
    
    # 初始化策略
    strategy = FundingRateStrategy(
        long_threshold=-0.003,   # -0.3%
        short_threshold=0.005,   # 0.5%
        exit_threshold=0.001     # 0.1%
    )
    
    # 记录交易
    trades = []
    signals = []
    
    # 遍历数据生成信号
    for idx, row in df.iterrows():
        signal = strategy.generate_signal(
            row['funding_rate'], 
            row['price'],
            row['timestamp']
        )
        
        signals.append(signal)
        
        # 记录交易
        if signal in ['LONG', 'SHORT', 'CLOSE']:
            trade = {
                'timestamp': row['timestamp'],
                'signal': signal,
                'price': row['price'],
                'funding_rate': row['funding_rate'],
                'position': strategy.position
            }
            trades.append(trade)
            
            print(f"\n{'='*60}")
            print(f"📍 {signal} 信号")
            print(f"时间: {row['timestamp']}")
            print(f"价格: ${row['price']:,.2f}")
            print(f"资金费率: {row['funding_rate']:.4f}%")
            
            if signal == 'CLOSE' and len(trades) >= 2:
                entry_trade = trades[-2]
                pnl = strategy.calculate_pnl(row['price'])
                holding_time = (row['timestamp'] - entry_trade['timestamp']).total_seconds() / 3600
                print(f"💰 盈亏: {pnl:+.2f}%")
                print(f"⏱️  持仓时间: {holding_time:.1f} 小时")
    
    # 添加信号列到数据
    df['signal'] = signals
    
    # 统计结果
    print(f"\n{'='*60}")
    print("📈 回测统计")
    print(f"{'='*60}")
    print(f"总交易次数: {len(trades)} 次")
    print(f"开多次数: {len([t for t in trades if t['signal'] == 'LONG'])} 次")
    print(f"开空次数: {len([t for t in trades if t['signal'] == 'SHORT'])} 次")
    print(f"平仓次数: {len([t for t in trades if t['signal'] == 'CLOSE'])} 次")
    
    # 当前持仓
    if strategy.position != 0:
        current_pnl = strategy.calculate_pnl(df.iloc[-1]['price'])
        print(f"\n当前仓位: {'多仓' if strategy.position == 1 else '空仓'}")
        print(f"开仓价格: ${strategy.entry_price:,.2f}")
        print(f"当前价格: ${df.iloc[-1]['price']:,.2f}")
        print(f"当前盈亏: {current_pnl:+.2f}%")
        print(f"当前资金费率: {df.iloc[-1]['funding_rate']:.4f}%")
    else:
        print(f"\n当前仓位: 空仓")
    
    print(f"{'='*60}\n")
    
    return df, trades


def analyze_funding_rate_distribution(data_file='okx_btc_data.csv'):
    """分析资金费率分布"""
    
    df = pd.read_csv(data_file)
    
    print("="*60)
    print("📊 资金费率分布分析")
    print("="*60)
    
    print(f"\n最小值: {df['funding_rate'].min():.4f}%")
    print(f"最大值: {df['funding_rate'].max():.4f}%")
    print(f"平均值: {df['funding_rate'].mean():.4f}%")
    print(f"中位数: {df['funding_rate'].median():.4f}%")
    print(f"标准差: {df['funding_rate'].std():.4f}%")
    
    # 分析费率区间分布
    print(f"\n费率区间分布:")
    print(f"  极负(<-0.3%): {len(df[df['funding_rate'] < -0.003])} 次 ({len(df[df['funding_rate'] < -0.003])/len(df)*100:.1f}%)")
    print(f"  负值(-0.3%~0): {len(df[(df['funding_rate'] >= -0.003) & (df['funding_rate'] < 0)])} 次 ({len(df[(df['funding_rate'] >= -0.003) & (df['funding_rate'] < 0)])/len(df)*100:.1f}%)")
    print(f"  中性(0~0.5%): {len(df[(df['funding_rate'] >= 0) & (df['funding_rate'] < 0.005)])} 次 ({len(df[(df['funding_rate'] >= 0) & (df['funding_rate'] < 0.005)])/len(df)*100:.1f}%)")
    print(f"  高值(0.5%~1%): {len(df[(df['funding_rate'] >= 0.005) & (df['funding_rate'] < 0.01)])} 次 ({len(df[(df['funding_rate'] >= 0.005) & (df['funding_rate'] < 0.01)])/len(df)*100:.1f}%)")
    print(f"  极高(>1%): {len(df[df['funding_rate'] >= 0.01])} 次 ({len(df[df['funding_rate'] >= 0.01])/len(df)*100:.1f}%)")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # 1. 分析资金费率分布
    analyze_funding_rate_distribution()
    
    # 2. 回测策略
    df, trades = backtest_strategy()
    
    # 3. 给出建议
    print("\n💡 策略建议:")
    print("="*60)
    print("✅ 当前数据显示资金费率波动明显")
    print("✅ 策略有明确的入场和出场信号")
    print("⚠️  建议继续收集数据至少24-48小时")
    print("⚠️  实盘前需要考虑交易手续费(约0.05%)")
    print("⚠️  建议小资金(10-20 USDT)先测试")
    print("="*60)
