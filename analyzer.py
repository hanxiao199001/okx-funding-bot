#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperliquid BTC数据分析框架
功能：数据加载、清洗、可视化、统计分析
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np

# 设置中文字体（Mac）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class HyperliquidAnalyzer:
    """Hyperliquid数据分析器"""
    
    def __init__(self, data_file='hyperliquid_btc_data.csv'):
        """初始化分析器"""
        self.data_file = data_file
        self.df = None
        
    def load_data(self):
        """加载并清洗数据"""
        print("📊 加载数据...")
        try:
            self.df = pd.read_csv(self.data_file)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df = self.df.sort_values('timestamp')
            
            print(f"✅ 成功加载 {len(self.df)} 条数据")
            print(f"📅 时间范围: {self.df['timestamp'].min()} 至 {self.df['timestamp'].max()}")
            return self.df
        except FileNotFoundError:
            print(f"❌ 文件不存在: {self.data_file}")
            return None
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return None
    
    def basic_stats(self):
        """基础统计分析"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        print("\n" + "="*60)
        print("📈 基础统计")
        print("="*60)
        
        # 价格统计
        print(f"\n【价格统计】")
        print(f"  最高价: ${self.df['price'].max():,.2f}")
        print(f"  最低价: ${self.df['price'].min():,.2f}")
        print(f"  平均价: ${self.df['price'].mean():,.2f}")
        print(f"  标准差: ${self.df['price'].std():,.2f}")
        print(f"  波动率: {(self.df['price'].std() / self.df['price'].mean() * 100):.2f}%")
        
        # 资金费率统计
        print(f"\n【资金费率统计】")
        print(f"  最高费率: {self.df['funding_rate'].max():.4f}%")
        print(f"  最低费率: {self.df['funding_rate'].min():.4f}%")
        print(f"  平均费率: {self.df['funding_rate'].mean():.4f}%")
        print(f"  正费率次数: {(self.df['funding_rate'] > 0).sum()} 次")
        print(f"  负费率次数: {(self.df['funding_rate'] < 0).sum()} 次")
        
        # 持仓量统计
        print(f"\n【持仓量统计】")
        print(f"  最大持仓: {self.df['open_interest'].max():,.0f}")
        print(f"  最小持仓: {self.df['open_interest'].min():,.0f}")
        print(f"  平均持仓: {self.df['open_interest'].mean():,.0f}")
        
        # 数据质量
        print(f"\n【数据质量】")
        print(f"  总数据量: {len(self.df)} 条")
        print(f"  缺失值: {self.df.isnull().sum().sum()} 个")
        print(f"  时间跨度: {(self.df['timestamp'].max() - self.df['timestamp'].min()).total_seconds() / 3600:.1f} 小时")
        
        print("="*60)
    
    def plot_price_trend(self, save_path='price_trend.png'):
        """绘制价格趋势图"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        plt.figure(figsize=(14, 6))
        plt.plot(self.df['timestamp'], self.df['price'], 
                linewidth=2, color='#2E86DE', marker='o', markersize=4)
        plt.title('BTC价格趋势', fontsize=16, fontweight='bold')
        plt.xlabel('时间', fontsize=12)
        plt.ylabel('价格 (USD)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"✅ 价格趋势图已保存: {save_path}")
        plt.close()
    
    def plot_funding_rate(self, save_path='funding_rate.png'):
        """绘制资金费率图"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        plt.figure(figsize=(14, 6))
        
        # 区分正负费率用不同颜色
        colors = ['#EE5A6F' if x > 0 else '#26DE81' for x in self.df['funding_rate']]
        plt.bar(self.df['timestamp'], self.df['funding_rate'], 
               color=colors, alpha=0.7, width=0.03)
        
        plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
        plt.title('资金费率变化', fontsize=16, fontweight='bold')
        plt.xlabel('时间', fontsize=12)
        plt.ylabel('资金费率 (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"✅ 资金费率图已保存: {save_path}")
        plt.close()
    
    def plot_combined(self, save_path='combined_analysis.png'):
        """绘制综合分析图（价格+资金费率双轴）"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # 价格曲线（左轴）
        color1 = '#2E86DE'
        ax1.set_xlabel('时间', fontsize=12)
        ax1.set_ylabel('价格 (USD)', color=color1, fontsize=12)
        ax1.plot(self.df['timestamp'], self.df['price'], 
                color=color1, linewidth=2, marker='o', markersize=4, label='价格')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3)
        
        # 资金费率（右轴）
        ax2 = ax1.twinx()
        color2 = '#FC5C65'
        ax2.set_ylabel('资金费率 (%)', color=color2, fontsize=12)
        ax2.plot(self.df['timestamp'], self.df['funding_rate'], 
                color=color2, linewidth=2, marker='s', markersize=4, 
                linestyle='--', label='资金费率')
        ax2.tick_params(axis='y', labelcolor=color2)
        ax2.axhline(y=0, color='gray', linestyle=':', linewidth=1)
        
        plt.title('BTC价格与资金费率综合分析', fontsize=16, fontweight='bold')
        fig.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"✅ 综合分析图已保存: {save_path}")
        plt.close()
    
    def plot_open_interest(self, save_path='open_interest.png'):
        """绘制持仓量趋势"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        plt.figure(figsize=(14, 6))
        plt.fill_between(self.df['timestamp'], self.df['open_interest'], 
                        alpha=0.5, color='#FD79A8')
        plt.plot(self.df['timestamp'], self.df['open_interest'], 
                linewidth=2, color='#E84393', marker='o', markersize=4)
        plt.title('持仓量趋势', fontsize=16, fontweight='bold')
        plt.xlabel('时间', fontsize=12)
        plt.ylabel('持仓量', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"✅ 持仓量图已保存: {save_path}")
        plt.close()
    
    def correlation_analysis(self):
        """相关性分析"""
        if self.df is None:
            print("❌ 请先加载数据")
            return
        
        print("\n" + "="*60)
        print("🔗 相关性分析")
        print("="*60)
        
        corr_matrix = self.df[['price', 'funding_rate', 'open_interest']].corr()
        print("\n相关系数矩阵:")
        print(corr_matrix)
        
        # 绘制相关性热力图
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', 
                   center=0, vmin=-1, vmax=1, square=True)
        plt.title('变量相关性热力图', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=300)
        print(f"\n✅ 相关性热力图已保存: correlation_heatmap.png")
        plt.close()
        
        print("="*60)
    
    def generate_full_report(self):
        """生成完整分析报告"""
        print("\n🚀 开始生成完整分析报告...")
        print("="*60)
        
        # 1. 加载数据
        self.load_data()
        if self.df is None:
            return
        
        # 2. 基础统计
        self.basic_stats()
        
        # 3. 生成所有图表
        print("\n📊 生成图表...")
        self.plot_price_trend()
        self.plot_funding_rate()
        self.plot_combined()
        self.plot_open_interest()
        
        # 4. 相关性分析
        self.correlation_analysis()
        
        print("\n" + "="*60)
        print("✅ 分析报告生成完成！")
        print("📁 生成的文件:")
        print("  - price_trend.png (价格趋势)")
        print("  - funding_rate.png (资金费率)")
        print("  - combined_analysis.png (综合分析)")
        print("  - open_interest.png (持仓量)")
        print("  - correlation_heatmap.png (相关性热力图)")
        print("="*60)


def main():
    """主函数 - 快速分析"""
    analyzer = HyperliquidAnalyzer()
    analyzer.generate_full_report()


if __name__ == "__main__":
    main()
