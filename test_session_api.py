from fastapi.testclient import TestClient
from main import app
import traceback

client = TestClient(app)

try:
    login_resp = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': '123'
    })
    print(f'Login: {login_resp.status_code}')

    if login_resp.status_code != 200:
        print(f'Login failed: {login_resp.text}')
        exit(1)

    token = login_resp.json()['access_token']
    print(f'Token: {token[:30]}...')

    resp = client.post(
        '/api/sessions/start',
        json={'assignment_id': 'cmu62dltn0001bln3q557t2wc', 'device_id': 'TEST'},
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f'Start session response: {resp.status_code}')
    print(f'Body: {resp.text}')

    if resp.status_code == 200:
        print('SUCCESS!')
        print(resp.json())
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
