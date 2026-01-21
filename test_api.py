#!/usr/bin/env python3
"""
OKX API 连接测试脚本
"""
import os
import requests
import hmac
import hashlib
import base64
import json
from datetime import datetime

class OKXAPITester:
    def __init__(self):
        # 从环境变量读取
        self.api_key = os.getenv('OKX_API_KEY')
        self.secret_key = os.getenv('OKX_SECRET_KEY')
        self.passphrase = os.getenv('OKX_PASSPHRASE')
        self.base_url = 'https://www.okx.com'
        
        # 如果环境变量没有，尝试从.env文件读取
        if not all([self.api_key, self.secret_key, self.passphrase]):
            self._load_from_env_file()
    
    def _load_from_env_file(self):
        """从.env文件加载配置"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key == 'OKX_API_KEY':
                            self.api_key = value
                        elif key == 'OKX_SECRET_KEY':
                            self.secret_key = value
                        elif key == 'OKX_PASSPHRASE':
                            self.passphrase = value
        except FileNotFoundError:
            pass
        
    def _get_signature(self, timestamp, method, request_path, body=''):
        """生成签名"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _get_headers(self, method, request_path, body=''):
        """生成请求头"""
        timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
        signature = self._get_signature(timestamp, method, request_path, body)
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """测试基础连接"""
        print("=" * 70)
        print("🔗 测试1: 基础连接（公开API）")
        print("=" * 70)
        
        try:
            url = f"{self.base_url}/api/v5/public/time"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 连接成功")
                print(f"服务器时间: {data['data'][0]['ts']}")
                return True
            else:
                print(f"❌ 连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False
    
    def test_authentication(self):
        """测试API认证"""
        print("\n" + "=" * 70)
        print("🔑 测试2: API认证")
        print("=" * 70)
        
        if not all([self.api_key, self.secret_key, self.passphrase]):
            print("❌ API配置不完整")
            print("  请先配置 .env 文件")
            return False
        
        try:
            request_path = '/api/v5/account/balance'
            headers = self._get_headers('GET', request_path)
            url = f"{self.base_url}{request_path}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    print(f"✅ 认证成功")
                    return True
                else:
                    print(f"❌ API返回错误: {data['msg']}")
                    return False
            else:
                print(f"❌ 认证失败: HTTP {response.status_code}")
                print(f"响应: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 认证错误: {e}")
            return False
    
    def test_account_info(self):
        """获取账户信息"""
        print("\n" + "=" * 70)
        print("💰 测试3: 账户信息")
        print("=" * 70)
        
        try:
            request_path = '/api/v5/account/balance'
            headers = self._get_headers('GET', request_path)
            url = f"{self.base_url}{request_path}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    print(f"✅ 获取成功")
                    
                    # 显示USDT余额
                    found_usdt = False
                    for detail in data['data'][0]['details']:
                        if detail['ccy'] == 'USDT':
                            found_usdt = True
                            print(f"\n【USDT账户】")
                            print(f"  可用余额: {float(detail['availBal']):.2f} USDT")
                            print(f"  冻结余额: {float(detail['frozenBal']):.2f} USDT")
                            print(f"  总权益: {float(detail['eq']):.2f} USDT")
                    
                    if not found_usdt:
                        print("\n⚠️  未找到USDT余额，请先充值")
                    
                    return True
                else:
                    print(f"❌ 获取失败: {data['msg']}")
                    return False
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 查询错误: {e}")
            return False
    
    def test_market_data(self):
        """测试市场数据"""
        print("\n" + "=" * 70)
        print("📊 测试4: 市场数据")
        print("=" * 70)
        
        try:
            url = f"{self.base_url}/api/v5/public/funding-rate"
            params = {'instId': 'BTC-USDT-SWAP'}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    print(f"✅ 获取成功")
                    rate_data = data['data'][0]
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 查询错误: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "🚀 " + "=" * 65)
        print("OKX API 完整测试")
        print("=" * 70 + "\n")
        
        results = []
        
        # 测试1: 基础连接
        results.append(('基础连接', self.test_connection()))
        
        # 测试2: 认证
        results.append(('API认证', self.test_authentication()))
        
        # 测试3: 账户信息
        if results[1][1]:  # 如果认证成功
            results.append(('账户信息', self.test_account_info()))
        
        # 测试4: 市场数据
        results.append(('市场数据', self.test_market_data()))
        
        # 总结
        print("\n" + "=" * 70)
        print("📋 测试总结")
        print("=" * 70)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name}: {status}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！可以开始实盘交易")
        else:
            print("\n⚠️  部分测试失败，请检查配置")
        
        print("=" * 70)

if __name__ == '__main__':
    tester = OKXAPITester()
    tester.run_all_tests()
