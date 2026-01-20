#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperliquid BTC数据爬虫 - 修复版
每小时采集：价格、资金费率、持仓量
"""

import requests
import pandas as pd
from datetime import datetime
import time
import schedule
import os
import json

# Hyperliquid API端点
API_BASE = "https://api.hyperliquid.xyz/info"

def fetch_btc_data():
    """获取BTC的价格、资金费率、持仓量"""
    try:
        # 获取市场数据
        meta_payload = {"type": "metaAndAssetCtxs"}
        response = requests.post(API_BASE, json=meta_payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"📡 API响应类型: {type(data)}")
        # 处理不同的响应格式
        if isinstance(data, list) and len(data) >= 2:
            # 格式1: [meta, assetCtxs]
            meta = data[0]
            asset_ctxs = data[1]
            
            # 查找BTC
            btc_index = None
            for idx, item in enumerate(meta.get('universe', [])):
                if item.get('name') == 'BTC':
                    btc_index = idx
                    break
                    
            
            if btc_index is not None and btc_index < len(asset_ctxs):
                btc_data = asset_ctxs[btc_index]
            else:
                print("❌ 未找到BTC数据")
                return None
                
        elif isinstance(data, dict):
            # 格式2: 直接字典
            btc_data = data
        else:
            print(f"❌ 未知的API响应格式: {json.dumps(data, indent=2)[:500]}")
            return None
        
        # 提取数据（兼容多种字段名）
        price = float(btc_data.get('markPx') or btc_data.get('mark_price') or btc_data.get('price', 0))
        open_interest = float(btc_data.get('openInterest') or btc_data.get('open_interest', 0))
        funding_rate = float(btc_data.get('funding') or btc_data.get('funding_rate', 0))
        
        if price == 0:
            print(f"⚠️  数据异常，BTC数据: {json.dumps(btc_data, indent=2)[:300]}")
            return None
        
        # 组装数据
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': price,
            'funding_rate': funding_rate * 100,  # 转换为百分比
            'open_interest': open_interest
        }
        
        print(f"✅ [{result['timestamp']}] 价格: ${price:,.2f} | 资金费率: {result['funding_rate']:.4f}% | 持仓量: {open_interest:,.0f}")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"❌ 数据解析失败: {e}")
        print(f"原始响应: {json.dumps(data, indent=2)[:500] if 'data' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def save_to_csv(data, filename='hyperliquid_btc_data.csv'):
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
    print("🚀 Hyperliquid BTC数据爬虫启动")
    print("📊 每小时运行一次,按 Ctrl+C 停止")
    print("="*60)
    
    # 立即执行一次
    job()
    
    # 设置每小时运行一次
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
