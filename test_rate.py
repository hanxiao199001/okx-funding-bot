import requests

response = requests.get('https://www.okx.com/api/v5/public/funding-rate',
                       params={'instId': 'BTC-USDT-SWAP'}, timeout=10)
print("状态码:", response.status_code)
data = response.json()
print("完整响应:", data)
if data['code'] == '0':
    rate = float(data['data'][0]['fundingRate'])
    print(f"\n原始费率: {rate}")
    print(f"百分比: {rate * 100}%")
