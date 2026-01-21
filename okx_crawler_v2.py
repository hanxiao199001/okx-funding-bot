#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX数据爬虫 - 优化版（带错误重试）
"""

import requests
import pandas as pd
from datetime import datetime
import time
import schedule

# API配置
API_BASE = "https://www.okx.com"
SYMBOL = "BTC-USDT-SWAP"
DATA_FILE = "okx_btc_data.csv"

# 重试配置
MAX_RETRIES = 5
RETRY_DELAY = 10  # 秒

def fetch_with_retry(url, params=None, retries=MAX_RETRIES):
    """带重试的HTTP请求"""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.SSLError as e:
            print(f"⚠️  SSL错误 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"⏳ {RETRY_DELAY}秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ 达到最大重试次数，跳过本次采集")
                return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️  网络错误 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"⏳ {RETRY_DELAY}秒后重试...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ 达到最大重试次数，跳过本次采集")
                return None
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            return None
    
    return None

def collect_data():
    """采集数据"""
    print("\n" + "="*60)
    
    try:
        # 获取价格
        ticker_url = f"{API_BASE}/api/v5/market/ticker"
        ticker_params = {"instId": SYMBOL}
        ticker_data = fetch_with_retry(ticker_url, params=ticker_params)
        
        if not ticker_data or ticker_data.get('code') != '0':
            print(f"❌ 获取价格失败")
            print("="*60)
            return
        
        price = float(ticker_data['data'][0]['last'])
        
        # 获取资金费率
        funding_url = f"{API_BASE}/api/v5/public/funding-rate"
        funding_params = {"instId": SYMBOL}
        funding_data = fetch_with_retry(funding_url, params=funding_params)
        
        if not funding_data or funding_data.get('code') != '0':
            print(f"❌ 获取资金费率失败")
            print("="*60)
            return
        
        funding_rate = float(funding_data['data'][0]['fundingRate']) * 100
        next_funding_time = funding_data['data'][0]['nextFundingTime']
        
        # 获取持仓量
        oi_url = f"{API_BASE}/api/v5/public/open-interest"
        oi_params = {"instId": SYMBOL}
        oi_data = fetch_with_retry(oi_url, params=oi_params)
        
        if not oi_data or oi_data.get('code') != '0':
            print(f"❌ 获取持仓量失败")
            print("="*60)
            return
        
        open_interest = float(oi_data['data'][0]['oi'])
        open_interest_usd = float(oi_data['data'][0]['oiCcy'])
        
        # 保存数据
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        new_data = {
            'timestamp': timestamp,
            'price': price,
            'funding_rate': funding_rate,
            'open_interest': open_interest,
            'open_interest_usd': open_interest_usd,
            'next_funding_time': next_funding_time
        }
        
        # 追加到CSV
        try:
            df = pd.DataFrame([new_data])
            df.to_csv(DATA_FILE, mode='a', header=False, index=False)
            
            print(f"✅ [{timestamp}] 价格: ${price:,.2f} | 资金费率: {funding_rate:.4f}% | 持仓量: {open_interest_usd:,.0f} USD")
            print(f"💾 数据已保存到 {DATA_FILE}")
            
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
    
    except Exception as e:
        print(f"❌ 采集过程出错: {e}")
    
    print("="*60)

def main():
    """主函数"""
    print("🚀 OKX BTC数据爬虫启动（优化版）")
    print("✨ 新功能：自动错误重试、网络故障恢复")
    print("📊 每5分钟运行一次，按 Ctrl+C 停止")
    print("="*60)
    
    # 初始化CSV（如果不存在）
    try:
        pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            'timestamp', 'price', 'funding_rate', 
            'open_interest', 'open_interest_usd', 'next_funding_time'
        ])
        df.to_csv(DATA_FILE, index=False)
        print(f"📁 创建新数据文件: {DATA_FILE}")
    
    # 立即执行一次
    collect_data()
    
    # 定时任务
    schedule.every(5).minutes.do(collect_data)
    
    print("\n⏰ 定时任务已启动，等待下一次采集...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  爬虫已停止")

if __name__ == "__main__":
    main()
