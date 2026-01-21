import os
import requests
import hmac
import hashlib
import base64
from datetime import datetime

with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            if key == 'OKX_API_KEY': api_key = value
            elif key == 'OKX_SECRET_KEY': secret_key = value
            elif key == 'OKX_PASSPHRASE': passphrase = value

request_path = '/api/v5/account/balance'
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
message = timestamp + 'GET' + request_path
mac = hmac.new(bytes(secret_key, encoding='utf8'),
              bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
signature = base64.b64encode(mac.digest()).decode()

headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

response = requests.get('https://www.okx.com' + request_path, headers=headers)
print("状态码:", response.status_code)
print("响应:", response.json())
