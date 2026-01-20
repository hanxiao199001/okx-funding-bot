#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证分析功能
"""

from analyzer import HyperliquidAnalyzer

def quick_test():
    """快速测试"""
    print("🧪 快速测试开始...")
    print("="*60)
    
    # 创建分析器
    analyzer = HyperliquidAnalyzer()
    
    # 加载数据
    df = analyzer.load_data()
    
    if df is not None and len(df) > 0:
        print("\n✅ 数据加载成功")
        print(f"📊 当前数据量: {len(df)} 条")
        print(f"📅 最新数据时间: {df['timestamp'].max()}")
        print(f"💰 最新价格: ${df['price'].iloc[-1]:,.2f}")
        print(f"📈 最新资金费率: {df['funding_rate'].iloc[-1]:.4f}%")
        
        # 基础统计
        analyzer.basic_stats()
        
        # 生成一张测试图
        print("\n📊 生成测试图表...")
        analyzer.plot_combined('test_combined.png')
        
        print("\n✅ 测试完成！框架运行正常！")
    else:
        print("\n⚠️  数据不足，等待爬虫收集更多数据...")
    
    print("="*60)

if __name__ == "__main__":
    quick_test()
