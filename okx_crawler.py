#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX BTC数据爬虫
每5分钟采集：价格、资金费率、持仓量
无需账户，公开API即可访问
"""

import requests
import pandas as pd
from datetime import datetime
import time
import schedule
import os

# OKX公开API端点
API_BASE = "https://www.okx.com"

def fetch_btc_data():
    """获取BTC的价格、资金费率、持仓量"""
    try:
        # 1. 获取BTC永续合约标记价格
        ticker_url = f"{API_BASE}/api/v5/market/ticker"
        ticker_params = {"instId": "BTC-USDT-SWAP"}
        ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)
        ticker_data = ticker_response.json()
        
        if ticker_data['code'] != '0':
            print(f"❌ 获取价格失败: {ticker_data.get('msg', 'Unknown error')}")
            return None
        
        price = float(ticker_data['data'][0]['last'])
        
        # 2. 获取资金费率
        funding_url = f"{API_BASE}/api/v5/public/funding-rate"
        funding_params = {"instId": "BTC-USDT-SWAP"}
        funding_response = requests.get(funding_url, params=funding_params, timeout=10)
        funding_data = funding_response.json()
        
        if funding_data['code'] != '0':
            print(f"❌ 获取资金费率失败: {funding_data.get('msg', 'Unknown error')}")
            return None
        
        funding_rate = float(funding_data['data'][0]['fundingRate']) * 100  # 转换为百分比
        next_funding_time = funding_data['data'][0]['nextFundingTime']
        
        # 3. 获取持仓量
        oi_url = f"{API_BASE}/api/v5/public/open-interest"
        oi_params = {"instId": "BTC-USDT-SWAP"}
        oi_response = requests.get(oi_url, params=oi_params, timeout=10)
        oi_data = oi_response.json()
        
        if oi_data['code'] != '0':
            print(f"❌ 获取持仓量失败: {oi_data.get('msg', 'Unknown error')}")
            return None
        
        open_interest = float(oi_data['data'][0]['oi'])  # 持仓量（张数）
        open_interest_usd = float(oi_data['data'][0]['oiCcy'])  # 持仓量（USD）
        
        # 组装数据
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': price,
            'funding_rate': funding_rate,
            'open_interest': open_interest,
            'open_interest_usd': open_interest_usd,
            'next_funding_time': next_funding_time
        }
        
        print(f"✅ [{result['timestamp']}] 价格: ${price:,.2f} | 资金费率: {funding_rate:.4f}% | 持仓量: {open_interest_usd:,.0f} USD")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"❌ 数据解析失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def save_to_csv(data, filename='okx_btc_data.csv'):
    """保存数据到CSV"""
    if data is None:
        return
    
    try:
        # 转换为DataFrame
        df = pd.DataFrame([data])
        
        # 如果文件存在,追加;否则创建新文件
        if os.path.exists(filename):
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)
        
        print(f"💾 数据已保存到 {filename}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def job():
    """定时任务:获取并保存数据"""
    print("\n" + "="*60)
    data = fetch_btc_data()
    save_to_csv(data)
    print("="*60)

def run_crawler():
    """运行爬虫"""
    print("🚀 OKX BTC数据爬虫启动")
    print("📊 每5分钟运行一次,按 Ctrl+C 停止")
    print("="*60)
    
    # 立即执行一次
    job()
    
    # 设置每5分钟运行一次
    schedule.every(5).minutes.do(job)
    
    # 循环检查
    while True:
        schedule.run_pending()
        time.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    try:
        run_crawler()
    except KeyboardInterrupt:
        print("\n\n⏹️  爬虫已停止")
