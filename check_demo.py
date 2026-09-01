import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ['DERIV_API_TOKEN']
app_id = os.environ['DERIV_APP_ID']

headers = {
    'Authorization': f'Bearer {token}',
    'Deriv-App-ID': app_id,
    'Content-Type': 'application/json'
}

resp = requests.get('https://api.derivws.com/trading/v1/options/accounts', headers=headers)
print(resp.json())
