#!/usr/bin/env python3
import os
import requests
import hmac
import hashlib
import base64
import time
from datetime import datetime

class OKXLiveBot:
    def __init__(self):
        self._load_env()
        self.base_url = 'https://www.okx.com'
        self.inst_id = 'BTC-USDT-SWAP'
        self.short_threshold = 0.3  # 0.3%（已改为百分比）
        self.exit_threshold = 0.1   # 0.1%
        self.stop_loss = 2.0        # 2%
        self.take_profit = 1.5      # 1.5%
    
    def _load_env(self):
        self.api_key = os.getenv('OKX_API_KEY')
        self.secret_key = os.getenv('OKX_SECRET_KEY')
        self.passphrase = os.getenv('OKX_PASSPHRASE')
        if not all([self.api_key, self.secret_key, self.passphrase]):
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key == 'OKX_API_KEY': self.api_key = value
                            elif key == 'OKX_SECRET_KEY': self.secret_key = value
                            elif key == 'OKX_PASSPHRASE': self.passphrase = value
            except: pass
    
    def _get_signature(self, timestamp, method, request_path, body=''):
        message = timestamp + method + request_path + body
        mac = hmac.new(bytes(self.secret_key, encoding='utf8'),
                      bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()
    
    def _get_headers(self, method, request_path, body=''):
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': self._get_signature(timestamp, method, request_path, body),
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def get_balance(self):
        try:
            request_path = '/api/v5/account/balance'
            headers = self._get_headers('GET', request_path)
            response = requests.get(f"{self.base_url}{request_path}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    for detail in data['data'][0]['details']:
                        if detail['ccy'] == 'USDT':
                            return float(detail['availBal'])
        except: pass
        return 0
    
    def get_market_data(self):
        try:
            response = requests.get(f"{self.base_url}/api/v5/market/ticker",
                                  params={'instId': self.inst_id}, timeout=10)
            price = float(response.json()['data'][0]['last']) if response.status_code == 200 else None
            
            response = requests.get(f"{self.base_url}/api/v5/public/funding-rate",
                                  params={'instId': self.inst_id}, timeout=10)
            rate = None
            if response.status_code == 200:
                rate_raw = float(response.json()['data'][0]['fundingRate'])
                rate = rate_raw * 100  # 转换成百分比
            return price, rate
        except: return None, None
    
    def get_position(self):
        try:
            request_path = f'/api/v5/account/positions?instId={self.inst_id}'
            headers = self._get_headers('GET', request_path)
            response = requests.get(f"{self.base_url}{request_path}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0' and len(data['data']) > 0:
                    pos = data['data'][0]
                    pos_size = float(pos['pos'])
                    if pos_size != 0:
                        return {
                            'side': 'SHORT' if pos_size < 0 else 'LONG',
                            'size': abs(pos_size),
                            'avg_price': float(pos['avgPx']),
                            'upl': float(pos['upl'])
                        }
        except: pass
        return None
    
    def check_and_display(self):
        price, rate = self.get_market_data()
        balance = self.get_balance()
        position = self.get_position()
        
        if price is None or rate is None:
            print("❌ 无法获取市场数据")
            return
        
        print(f"\n{'='*60}\n📊 实盘监控 - {datetime.now().strftime('%H:%M:%S')}\n{'='*60}")
        print(f"价格: ${price:,.2f} | 费率: {rate:.2f}% | 余额: {balance:.2f} USDT")
        
        if position:
            pnl_pct = ((position['avg_price'] - price) / position['avg_price'] * 100 
                      if position['side'] == 'SHORT' else 
                      (price - position['avg_price']) / position['avg_price'] * 100)
            print(f"\n【持仓】{position['side']} | 开仓: ${position['avg_price']:,.2f}")
            print(f"浮盈: ${position['upl']:,.2f} ({pnl_pct:+.2f}%)")
            
            if pnl_pct >= self.take_profit:
                print(f"\n🔔 达到止盈 ({pnl_pct:+.2f}%) - 建议平仓")
            elif pnl_pct <= -self.stop_loss:
                print(f"\n🛑 触及止损 ({pnl_pct:+.2f}%) - 立即平仓!")
            elif rate < self.exit_threshold:
                print(f"\n⚠️ 费率降低 ({rate:.2f}%) - 考虑平仓")
            else:
                print(f"\n✅ 继续持有")
        else:
            print(f"\n【持仓】空仓")
            if rate > self.short_threshold:
                print(f"\n🔔 做空信号! 费率 {rate:.2f}% > 0.3%")
                print(f"💡 建议: OKX开空 6 USDT (30%资金)")
            else:
                print(f"\n⏳ 等待信号 (需要 > 0.3%，当前 {rate:.2f}%)")
        print(f"{'='*60}\n")
    
    def run(self):
        print("\n🤖 OKX 实盘监控 v1.1 (费率已修复)\n")
        try:
            while True:
                self.check_and_display()
                print("5分钟后更新...\n")
                time.sleep(300)
        except KeyboardInterrupt:
            print("\n👋 已停止")

if __name__ == '__main__':
    OKXLiveBot().run()
