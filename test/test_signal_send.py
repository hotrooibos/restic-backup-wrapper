# Run server first : $signal-cli -a +33123456789 daemon --http=localhost:8080

import json
import requests

# Preparing the request
url = 'http://localhost:8080/api/v1/rpc'
account = '+33123456789'
recipient = '+33123456789'
message = 'Hello from Python!'

payload = {
    'jsonrpc': '2.0',
    'method': 'send',
    'params': {
        'recipient': [recipient],
        'message': message
    },
    'id': 1
}

headers = {
    'Content-Type': 'application/json'
}

# Sending the request
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Handling the response
if response.status_code == 200:
    print('Message sent successfully!')
    print('Response:', response.json())
else:
    print('Failed to send message')
    print('Status code:', response.status_code)
    print('Response:', response.text)