#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX自动交易系统
功能：连接API、自动下单、仓位管理、风险控制
"""

import requests
import hmac
import base64
import json
from datetime import datetime, timezone
import time

class OKXTrader:
    """OKX交易客户端"""
    
    def __init__(self, api_key, secret_key, passphrase, is_demo=True):
        """
        初始化交易客户端
        
        参数：
        - api_key: API密钥
        - secret_key: 密钥
        - passphrase: API密码
        - is_demo: 是否使用模拟盘（True=模拟，False=实盘）
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        
        # API端点
        if is_demo:
            self.base_url = "https://www.okx.com"  # 模拟盘
            print("⚠️  当前使用：模拟交易环境")
        else:
            self.base_url = "https://www.okx.com"  # 实盘
            print("🔴 当前使用：实盘交易环境")
        
        # 交易参数
        self.symbol = "BTC-USDT-SWAP"  # BTC永续合约
        self.position = None  # 当前持仓
        
    def _sign(self, timestamp, method, request_path, body=''):
        """生成签名"""
        if body:
            body = json.dumps(body)
        
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _request(self, method, endpoint, params=None, data=None):
        """发送API请求"""
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        request_path = endpoint
        
        if params:
            request_path += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        signature = self._sign(timestamp, method, request_path, data or '')
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        url = self.base_url + request_path
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"❌ API请求失败: {e}")
            return None
    
    def get_account_balance(self):
        """获取账户余额"""
        endpoint = "/api/v5/account/balance"
        result = self._request('GET', endpoint)
        
        if result and result['code'] == '0':
            # 解析USDT余额
            for detail in result['data'][0]['details']:
                if detail['ccy'] == 'USDT':
                    return {
                        'available': float(detail['availBal']),
                        'frozen': float(detail['frozenBal']),
                        'total': float(detail['eq'])
                    }
        return None
    
    def get_position(self):
        """获取当前持仓"""
        endpoint = "/api/v5/account/positions"
        params = {"instId": self.symbol}
        result = self._request('GET', endpoint, params=params)
        
        if result and result['code'] == '0' and result['data']:
            pos = result['data'][0]
            return {
                'side': pos['posSide'],  # long/short
                'size': float(pos['pos']),
                'avg_price': float(pos['avgPx']),
                'unrealized_pnl': float(pos['upl']),
                'unrealized_pnl_ratio': float(pos['uplRatio']) * 100
            }
        return None
    
    def place_order(self, side, size, order_type='market', price=None):
        """
        下单
        
        参数：
        - side: 'buy' 或 'sell'
        - size: 下单数量（张数）
        - order_type: 'market'市价单 或 'limit'限价单
        - price: 限价单价格
        """
        endpoint = "/api/v5/trade/order"
        
        data = {
            "instId": self.symbol,
            "tdMode": "cross",  # 全仓模式
            "side": side,
            "ordType": order_type,
            "sz": str(size)
        }
        
        if order_type == 'limit' and price:
            data['px'] = str(price)
        
        result = self._request('POST', endpoint, data=data)
        
        if result and result['code'] == '0':
            order_id = result['data'][0]['ordId']
            print(f"✅ 下单成功！订单ID: {order_id}")
            return order_id
        else:
            error_msg = result.get('msg', 'Unknown error') if result else 'Network error'
            print(f"❌ 下单失败: {error_msg}")
            return None
    
    def close_position(self):
        """平仓"""
        pos = self.get_position()
        if not pos:
            print("⚠️  当前无持仓")
            return False
        
        # 确定平仓方向
        if pos['side'] == 'long':
            side = 'sell'
        else:
            side = 'buy'
        
        print(f"📍 平仓: {pos['side']} {pos['size']}张")
        return self.place_order(side, abs(pos['size']))
    
    def calculate_position_size(self, balance, price, leverage=1):
        """
        计算开仓数量
        
        参数：
        - balance: 可用余额（USDT）
        - price: 当前价格
        - leverage: 杠杆倍数
        
        返回：张数
        """
        # OKX BTC永续：1张 = 0.01 BTC = 100 USD
        contract_value = 100
        
        # 使用一定比例的余额（例如30%）
        use_balance = balance * 0.3
        
        # 计算张数
        size = int((use_balance * leverage) / contract_value)
        
        return max(1, size)  # 至少1张


class AutoTradingBot:
    """自动交易机器人"""
    
    def __init__(self, trader, strategy_params=None):
        """
        初始化机器人
        
        参数：
        - trader: OKXTrader实例
        - strategy_params: 策略参数字典
        """
        self.trader = trader
        
        # 策略参数
        if strategy_params is None:
            strategy_params = {
                'long_threshold': -0.003,
                'short_threshold': 0.005,
                'exit_threshold': 0.001,
                'stop_loss': -2.0,  # 止损线 -2%
                'take_profit': 1.5  # 止盈线 +1.5%
            }
        
        self.params = strategy_params
        self.position = None
        self.entry_price = None
        self.entry_time = None
    
    def get_market_data(self):
        """获取市场数据（资金费率、价格）"""
        # 这里使用公开API（无需签名）
        try:
            # 价格
            ticker_url = f"{self.trader.base_url}/api/v5/market/ticker"
            ticker_params = {"instId": self.trader.symbol}
            ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)
            ticker_data = ticker_response.json()
            price = float(ticker_data['data'][0]['last'])
            
            # 资金费率
            funding_url = f"{self.trader.base_url}/api/v5/public/funding-rate"
            funding_params = {"instId": self.trader.symbol}
            funding_response = requests.get(funding_url, params=funding_params, timeout=10)
            funding_data = funding_response.json()
            funding_rate = float(funding_data['data'][0]['fundingRate']) * 100
            
            return {
                'price': price,
                'funding_rate': funding_rate,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"❌ 获取市场数据失败: {e}")
            return None
    
    def check_signal(self, market_data):
        """检查交易信号"""
        funding_rate = market_data['funding_rate']
        price = market_data['price']
        
        # 无持仓 - 检查入场信号
        if self.position is None:
            if funding_rate < self.params['long_threshold']:
                return 'LONG'
            elif funding_rate > self.params['short_threshold']:
                return 'SHORT'
            return 'WAIT'
        
        # 有持仓 - 检查出场信号
        pos = self.trader.get_position()
        if not pos:
            self.position = None
            return 'WAIT'
        
        pnl_ratio = pos['unrealized_pnl_ratio']
        
        # 止损
        if pnl_ratio < self.params['stop_loss']:
            return 'CLOSE'
        
        # 止盈
        if pnl_ratio > self.params['take_profit']:
            return 'CLOSE'
        
        # 资金费率回归
        if abs(funding_rate) < self.params['exit_threshold']:
            return 'CLOSE'
        
        return 'HOLD'
    
    def execute_signal(self, signal, market_data):
        """执行交易信号"""
        
        if signal == 'LONG':
            print(f"\n🟢 开多信号触发")
            print(f"价格: ${market_data['price']:,.2f}")
            print(f"资金费率: {market_data['funding_rate']:.4f}%")
            
            # 获取余额
            balance = self.trader.get_account_balance()
            if not balance:
                print("❌ 无法获取账户余额")
                return
            
            # 计算仓位
            size = self.trader.calculate_position_size(
                balance['available'],
                market_data['price']
            )
            
            print(f"开仓数量: {size}张")
            
            # 下单
            order_id = self.trader.place_order('buy', size)
            if order_id:
                self.position = 'LONG'
                self.entry_price = market_data['price']
                self.entry_time = market_data['timestamp']
        
        elif signal == 'SHORT':
            print(f"\n🔴 开空信号触发")
            print(f"价格: ${market_data['price']:,.2f}")
            print(f"资金费率: {market_data['funding_rate']:.4f}%")
            
            balance = self.trader.get_account_balance()
            if not balance:
                print("❌ 无法获取账户余额")
                return
            
            size = self.trader.calculate_position_size(
                balance['available'],
                market_data['price']
            )
            
            print(f"开仓数量: {size}张")
            
            order_id = self.trader.place_order('sell', size)
            if order_id:
                self.position = 'SHORT'
                self.entry_price = market_data['price']
                self.entry_time = market_data['timestamp']
        
        elif signal == 'CLOSE':
            print(f"\n⚪ 平仓信号触发")
            
            pos = self.trader.get_position()
            if pos:
                print(f"当前盈亏: {pos['unrealized_pnl_ratio']:+.2f}%")
            
            success = self.trader.close_position()
            if success:
                self.position = None
                self.entry_price = None
                self.entry_time = None
    
    def run_once(self):
        """运行一次检查"""
        print(f"\n{'='*70}")
        print(f"🤖 自动交易检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # 获取市场数据
        market_data = self.get_market_data()
        if not market_data:
            return
        
        # 显示当前状态
        print(f"\n【市场状态】")
        print(f"价格: ${market_data['price']:,.2f}")
        print(f"资金费率: {market_data['funding_rate']:.4f}%")
        
        # 显示持仓
        pos = self.trader.get_position()
        if pos:
            print(f"\n【当前持仓】")
            print(f"方向: {pos['side']}")
            print(f"数量: {pos['size']}张")
            print(f"开仓价: ${pos['avg_price']:,.2f}")
            print(f"盈亏: {pos['unrealized_pnl_ratio']:+.2f}%")
        else:
            print(f"\n【当前持仓】无")
        
        # 检查信号
        signal = self.check_signal(market_data)
        print(f"\n【信号】{signal}")
        
        # 执行
        if signal in ['LONG', 'SHORT', 'CLOSE']:
            self.execute_signal(signal, market_data)
        
        print(f"{'='*70}")
    
    def run_continuous(self, interval=60):
        """持续运行"""
        print(f"🚀 自动交易机器人启动")
        print(f"⏰ 检查间隔: {interval}秒")
        print(f"⌨️  按 Ctrl+C 停止\n")
        
        try:
            while True:
                self.run_once()
                print(f"\n⏳ 等待 {interval} 秒...\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  机器人已停止")


# 使用示例
if __name__ == "__main__":
    print("="*70)
    print("🤖 OKX自动交易系统")
    print("="*70)
    print("\n⚠️  当前为示例代码，需要配置API密钥后使用")
    print("\n使用步骤：")
    print("1. 在OKX获取API密钥")
    print("2. 修改下方的API_KEY、SECRET_KEY、PASSPHRASE")
    print("3. 运行脚本")
    print("\n" + "="*70)
    
    # TODO: 替换为你的API密钥
    API_KEY = "7a1b11e5-173c-42a7-bd1b-cb58565b006f"
    SECRET_KEY = "0D16AD24DE311D06A2254F1D4231EA0D"
    PASSPHRASE = "HANxiao456258~"
    
# 初始化交易客户端（模拟盘）
trader = OKXTrader(API_KEY, SECRET_KEY, PASSPHRASE, is_demo=True)

# 初始化机器人
bot = AutoTradingBot(trader)

# 运行一次
bot.run_once()    
    # 运行一次
    # bot.run_once()
    
    # 或持续运行
    # bot.run_continuous(interval=60)
