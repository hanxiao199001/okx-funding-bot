#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时交易仪表盘
显示：持仓状态、盈亏、信号、系统健康度
"""

import requests
import pandas as pd
from datetime import datetime
import os
import json

def get_market_data():
    """获取市场数据"""
    try:
        # 价格
        r1 = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP", timeout=5)
        price = float(r1.json()['data'][0]['last'])
        
        # 资金费率
        r2 = requests.get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP", timeout=5)
        rate = float(r2.json()['data'][0]['fundingRate']) * 100
        
        # 持仓量
        r3 = requests.get("https://www.okx.com/api/v5/public/open-interest?instId=BTC-USDT-SWAP", timeout=5)
        oi = float(r3.json()['data'][0]['oiCcy'])
        
        return {
            'price': price,
            'funding_rate': rate,
            'open_interest': oi,
            'timestamp': datetime.now()
        }
    except Exception as e:
        return None

def get_data_collection_status():
    """获取数据采集状态"""
    if not os.path.exists('okx_btc_data.csv'):
        return None
    
    df = pd.read_csv('okx_btc_data.csv')
    
    # 最新数据
    latest = df.iloc[-1]
    
    # 时间跨度
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
    
    # 数据质量
    recent_df = df.tail(12)  # 最近1小时
    avg_interval = recent_df['timestamp'].diff().mean().total_seconds() / 60
    
    return {
        'total_records': len(df),
        'time_span_hours': time_span,
        'latest_time': latest['timestamp'],
        'avg_interval_minutes': avg_interval,
        'is_healthy': avg_interval < 10  # 采集间隔<10分钟为健康
    }

def calculate_strategy_stats():
    """计算策略统计"""
    if not os.path.exists('okx_btc_data.csv'):
        return None
    
    df = pd.read_csv('okx_btc_data.csv')
    
    # 资金费率统计
    current_rate = df.iloc[-1]['funding_rate']
    
    # 计算信号频率
    high_rate_count = len(df[df['funding_rate'] > 0.005])
    low_rate_count = len(df[df['funding_rate'] < -0.003])
    
    return {
        'current_rate': current_rate,
        'high_rate_percent': high_rate_count / len(df) * 100,
        'low_rate_percent': low_rate_count / len(df) * 100,
        'avg_rate': df['funding_rate'].mean(),
        'max_rate': df['funding_rate'].max(),
        'min_rate': df['funding_rate'].min()
    }

def display_dashboard():
    """显示仪表盘"""
    
    print("\n" + "="*70)
    print(" "*25 + "交易系统仪表盘")
    print("="*70)
    
    # 1. 市场数据
    market = get_market_data()
    if market:
        print("\n【市场数据】")
        print(f"时间: {market['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"BTC价格: ${market['price']:,.2f}")
        print(f"资金费率: {market['funding_rate']:.4f}%", end="")
        
        if market['funding_rate'] > 0.005:
            print(" (极高-做空信号)")
        elif market['funding_rate'] < -0.003:
            print(" (极低-做多信号)")
        else:
            print(" (中性)")
        
        print(f"持仓量: ${market['open_interest']:,.0f}")
    
    # 2. 数据采集状态
    data_status = get_data_collection_status()
    
    if data_status:
        print("\n【数据采集状态】")
        print(f"总数据量: {data_status['total_records']} 条")
        print(f"时间跨度: {data_status['time_span_hours']:.1f} 小时")
        print(f"最新采集: {data_status['latest_time']}")
        print(f"采集间隔: {data_status['avg_interval_minutes']:.1f} 分钟", end="")
        
        if data_status['is_healthy']:
            print(" (正常)")
        else:
            print(" (异常)")
    
    # 3. 策略统计
    stats = calculate_strategy_stats()
    
    if stats:
        print("\n【策略统计】")
        print(f"当前费率: {stats['current_rate']:.4f}%")
        print(f"平均费率: {stats['avg_rate']:.4f}%")
        print(f"费率区间: {stats['min_rate']:.4f}% ~ {stats['max_rate']:.4f}%")
        print(f"做空信号频率: {stats['high_rate_percent']:.1f}%")
        print(f"做多信号频率: {stats['low_rate_percent']:.1f}%")
    
    print("\n" + "="*70)
    print("最后更新: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*70 + "\n")

if __name__ == "__main__":
    display_dashboard()
